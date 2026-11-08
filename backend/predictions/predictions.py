# main_app/backend/predictions/predictions.py
import numpy as np
import supervision as sv
from ultralytics.trackers.utils.kalman_filter import KalmanFilterXYAH


class Predictions:
    def __init__(self, frames_to_predict: int = 30, max_missed: int = 30):
        self.predictors = ["kalman filter"]
        self.current_predictor = None
        self.kf = KalmanFilterXYAH()
        self.frames_to_predict = frames_to_predict
        self.max_missed = max_missed      # po ilu klatkach bez detekcji usunąć ślad
        self.tracks = {}                  # {track_id: {"mean", "cov", "missed"}}
        self.trajectories = {}            # {track_id: ndarray (N, 2)} do rysowania

    def change_predictor(self, text):
        print(f"zmiena predykcji z: {self.current_predictor} na: {text}")
        if self.current_predictor == text:
            self.current_predictor = None
        if text in self.predictors:
            self.current_predictor = text
        self.reset()
        print(f"predictor zmieniony: {self.current_predictor}")

    
    def reset(self):
        self.tracks.clear()
        self.trajectories.clear()

    def set_horizon(self, frames: int):
        self.frames_to_predict = max(1, int(frames))

    @staticmethod
    def _xyxy_to_xyah(box):
        x1, y1, x2, y2 = box
        w, h = x2 - x1, y2 - y1
        h = max(h, 1e-3)
        return np.array([x1 + w / 2.0, y1 + h / 2.0, w / h, h], dtype=np.float64)

    @staticmethod
    def _state_to_xyxy(mean):
        x, y, a, h = mean[:4]
        h = max(h, 1.0)
        w = max(a * h, 1.0)
        return [x - w / 2.0, y - h / 2.0, x + w / 2.0, y + h / 2.0]

    def predict(self, tracked, class_names, frames_ahead=None):
        """
        tracked:     sv.Detections z tracker_id (wynik Tracking_algorithms.track_cars)
        class_names: dict {class_id: nazwa}
        zwraca:      (sv.Detections z pozycją za `frames_ahead` klatek, labels)
        """
        n = frames_ahead or self.frames_to_predict
        if tracked is None or len(tracked) == 0 or tracked.tracker_id is None:
            self._age_tracks(set())
            return None, None

        seen = set()
        xyxy_list, id_list, conf_list, cls_list = [], [], [], []
        self.trajectories = {}

        confidences = (tracked.confidence if tracked.confidence is not None
                       else np.ones(len(tracked), dtype=np.float32))

        for box, tid, cid, conf in zip(tracked.xyxy, tracked.tracker_id,
                                       tracked.class_id, confidences):
            tid = int(tid)
            measurement = self._xyxy_to_xyah(box)

            if tid not in self.tracks:
                mean, cov = self.kf.initiate(measurement)
            else:
                mean, cov = self.kf.predict(self.tracks[tid]["mean"],
                                            self.tracks[tid]["cov"])
                mean, cov = self.kf.update(mean, cov, measurement)

            self.tracks[tid] = {"mean": mean, "cov": cov, "missed": 0}
            seen.add(tid)

            # predykcja na n klatek do przodu (na kopiach, stan śladu bez zmian)
            f_mean, f_cov = mean.copy(), cov.copy()
            path = []
            for _ in range(n):
                f_mean, f_cov = self.kf.predict(f_mean, f_cov)
                path.append(f_mean[:2].copy())

            self.trajectories[tid] = np.array(path)
            xyxy_list.append(self._state_to_xyxy(f_mean))
            id_list.append(tid)
            conf_list.append(float(conf))
            cls_list.append(int(cid))

        self._age_tracks(seen)

        detections = sv.Detections(
            xyxy=np.array(xyxy_list, dtype=np.float32),
            confidence=np.array(conf_list, dtype=np.float32),
            class_id=np.array(cls_list, dtype=int),
            tracker_id=np.array(id_list, dtype=int),
        )
        labels = [
            f"ID {tid} {class_names.get(cid, cid)} +{n}kl"
            for tid, cid in zip(detections.tracker_id, detections.class_id)
        ]
        return detections, labels

    def _age_tracks(self, seen):
        for tid in list(self.tracks):
            if tid in seen:
                continue
            self.tracks[tid]["missed"] += 1
            if self.tracks[tid]["missed"] > self.max_missed:
                del self.tracks[tid]