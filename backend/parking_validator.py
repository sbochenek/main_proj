import numpy as np
from collections import deque
from dataclasses import dataclass


@dataclass
class TrackState:
    history: deque
    missed: int = 0
    was_moving: bool = False      # ostatni znany status = "W ruchu"
    stopped_frames: int = 0       # ile klatek stoi od momentu zatrzymania


class ParkingValidator:
    STATUS_OK = "Poprawne parkowanie"
    STATUS_BAD = "Niepoprawne parkowanie"
    STATUS_MOVING = "W ruchu"
    STATUS_NEW = "Nowe wykrycie"
    STATUS_MULTI = "Zajmuje wiele miejsc"

    def __init__(
        self,
        fps: float = 10.0,
        overlap_threshold: float = 0.4,   # min. część auta w miejscu, żeby uznać parkowanie
        multi_spot_threshold: float = 0.25,  # min. część auta w kolejnym miejscu, żeby uznać je za zajęte
        spot_dedup_iou: float = 0.5,      # boxy miejsc o IoU >= tej wartości = to samo miejsce
        movement_ratio: float = 0.10,
        window_s: float = 1.5,
        grace_s: float = 3.0,
        moving_hold_s: float = 30.0,
    ):
        self.overlap_threshold = overlap_threshold
        self.multi_spot_threshold = multi_spot_threshold
        self.spot_dedup_iou = spot_dedup_iou
        self.movement_ratio = movement_ratio
        self.window = max(2, round(window_s * fps))
        self.grace = round(grace_s * fps)
        self.moving_hold = round(moving_hold_s * fps)
        self.smooth_k = max(1, self.window // 5)
        self.tracks: dict[int, TrackState] = {}

    # ---------- geometria ----------
    @staticmethod
    def calculate_coverage(car_box, parking_box) -> float:
        """Jaka część auta znajduje się w miejscu parkingowym."""
        cx1, cy1, cx2, cy2 = car_box
        px1, py1, px2, py2 = parking_box

        ix1 = max(cx1, px1); iy1 = max(cy1, py1)
        ix2 = min(cx2, px2); iy2 = min(cy2, py2)
        intersection = max(0, ix2 - ix1) * max(0, iy2 - iy1)

        car_area = max(0, cx2 - cx1) * max(0, cy2 - cy1)
        if car_area == 0:
            return 0.0
        return intersection / car_area

    @staticmethod
    def _iou(a, b) -> float:
        ix1 = max(a[0], b[0]); iy1 = max(a[1], b[1])
        ix2 = min(a[2], b[2]); iy2 = min(a[3], b[3])
        inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
        area_a = max(0, a[2] - a[0]) * max(0, a[3] - a[1])
        area_b = max(0, b[2] - b[0]) * max(0, b[3] - b[1])
        union = area_a + area_b - inter
        return inter / union if union > 0 else 0.0

    def _count_occupied_spots(self, car_box, parking_detections) -> tuple[int, float]:
        """
        Zwraca (liczba zajętych miejsc, największe pokrycie auta jednym miejscem).
        Miejsce jest zajęte, gdy pokrywa >= multi_spot_threshold powierzchni auta.
        Zdublowane boxy miejsc (wysokie IoU) liczone są jako jedno miejsce.
        """
        if parking_detections is None or len(parking_detections) == 0:
            return 0, 0.0

        candidates = []
        for parking_box in parking_detections.xyxy:
            cov = self.calculate_coverage(car_box, parking_box)
            if cov >= self.multi_spot_threshold:
                candidates.append((cov, parking_box))
        if not candidates:
            return 0, 0.0

        candidates.sort(key=lambda t: t[0], reverse=True)
        kept = []
        for cov, box in candidates:
            if all(self._iou(box, k) < self.spot_dedup_iou for _, k in kept):
                kept.append((cov, box))
        return len(kept), kept[0][0]

    # ---------- ruch ----------
    def _update_track(self, track_id, car_box) -> TrackState:
        x1, y1, x2, y2 = car_box
        center = np.array([(x1 + x2) / 2, (y1 + y2) / 2])
        state = self.tracks.get(track_id)
        if state is None:
            state = TrackState(history=deque(maxlen=self.window))
            self.tracks[track_id] = state
        state.history.append((center, max(x2 - x1, 1.0)))
        state.missed = 0
        return state

    def _has_moved(self, state: TrackState) -> bool:
        k = self.smooth_k
        centers = [c for c, _ in state.history]
        start = np.mean(centers[:k], axis=0)
        end = np.mean(centers[-k:], axis=0)
        size = np.median([s for _, s in state.history])
        return float(np.linalg.norm(end - start)) / size >= self.movement_ratio

    # ---------- główna logika ----------
    def validate(self, car_detections, parking_detections, tracking_enabled):
        """
        Zwraca (car_detections, labels) tej samej długości.
        car_detections może być None/empty -> (car_detections, [])
        """
        if car_detections is None or len(car_detections) == 0:
            self._age_tracks(set())
            return car_detections, []

        labels: list[str] = []
        tracker_ids = car_detections.tracker_id
        active_ids = set()

        for i, car_box in enumerate(car_detections.xyxy):
            n_spots, best_cov = self._count_occupied_spots(car_box, parking_detections)

            track_id = None
            if tracking_enabled and tracker_ids is not None:
                raw = tracker_ids[i]
                if raw is not None and int(raw) != -1:
                    track_id = int(raw)

            state = None
            if track_id is not None:
                active_ids.add(track_id)
                state = self._update_track(track_id, car_box)

            status = self._decide_status(state, n_spots, best_cov)
            labels.append(f"ID {track_id}: {status}" if track_id is not None else status)

        self._age_tracks(active_ids)
        return car_detections, labels

    def _decide_status(self, state: TrackState | None, n_spots: int, best_cov: float) -> str:
        overlap = best_cov >= self.overlap_threshold

        # Auto zajmuje >= 2 miejsc
        if n_spots >= 2:
            if state is None:
                return self.STATUS_MULTI
            if len(state.history) < self.window:
                return self.STATUS_NEW                  # nie oceniaj nowych aut
            if self._has_moved(state):
                state.was_moving = True                 # przejazd przez miejsca to nie parkowanie
                state.stopped_frames = 0
                return self.STATUS_MOVING
            state.was_moving = False
            state.stopped_frames = 0
            return self.STATUS_MULTI

        # Auto w jednym miejscu parkingowym -> OK
        if overlap:
            if state is not None:
                state.was_moving = False
                state.stopped_frames = 0
            return self.STATUS_OK

        # Brak ID -> nie da się ocenić ruchu
        if state is None:
            return self.STATUS_BAD

        # Nowe wykrycie
        if len(state.history) < self.window:
            return self.STATUS_NEW

        # Ruch
        if self._has_moved(state):
            state.was_moving = True
            state.stopped_frames = 0
            return self.STATUS_MOVING

        # Stoi poza miejscem, ale wcześniej jechało -> trzymaj "W ruchu"
        if state.was_moving and state.stopped_frames < self.moving_hold:
            state.stopped_frames += 1
            return self.STATUS_MOVING

        return self.STATUS_BAD

    def _age_tracks(self, active_ids: set):
        for tid in list(self.tracks):
            if tid in active_ids:
                continue
            state = self.tracks[tid]
            state.missed += 1
            if state.missed > self.grace:
                del self.tracks[tid]

    def reset(self):
        self.tracks.clear()