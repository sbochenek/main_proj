import numpy as np
from collections import deque

class ParkingValidator:
    def __init__(self, overlap_threshold=0.4, movement_ratio=0.05, window=15, grace=30):
        self.overlap_threshold = overlap_threshold
        self.movement_ratio = movement_ratio      # ułamek szerokości boxa w oknie
        self.window = window                      # liczba klatek
        self.grace = grace                        # ile klatek trzymać stan zgubionego ID
        self.history: dict[int, deque] = {}
        self.missed: dict[int, int] = {}

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

    def check_parking_overlap(self, car_box, parking_detections) -> bool:
        if parking_detections is None or len(parking_detections) == 0:
            return False
        for parking_box in parking_detections.xyxy:
            if self.calculate_coverage(car_box, parking_box) >= self.overlap_threshold:
                return True
        return False

    def check_movement(self, track_id, car_box) -> bool:
        x1, y1, x2, y2 = car_box
        center = np.array([(x1 + x2) / 2, (y1 + y2) / 2])
        size = max(x2 - x1, 1.0)
        hist = self.history.setdefault(track_id, deque(maxlen=self.window))
        hist.append(center)
        self.missed[track_id] = 0
        if len(hist) < self.window:
            return False                          # za mało danych, nie zgaduj
        displacement = float(np.linalg.norm(hist[-1] - hist[0]))
        return displacement / size >= self.movement_ratio

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
            # 1) nakładanie na miejsce parkingowe
            overlap = self.check_parking_overlap(car_box, parking_detections)

            # 2) track_id - bezpiecznie
            track_id = None
            if tracking_enabled and tracker_ids is not None:
                raw = tracker_ids[i]
                if raw is not None and int(raw) != -1:
                    track_id = int(raw)

            # 3) ruch w oknie czasowym (tylko gdy jest ID)
            moved = False
            if track_id is not None:
                active_ids.add(track_id)
                moved = self.check_movement(track_id, car_box)

            # 4) decyzja
            if overlap:
                status = "Poprawne parkowanie"
            elif moved:
                status = "W ruchu"
            else:
                status = "Niepoprawne parkowanie"

            labels.append(f"ID {track_id}: {status}" if track_id is not None else status)

        # 5) sprzątanie ID, które zniknęły (z okresem karencji)
        self._age_tracks(active_ids)
        return car_detections, labels

    def _age_tracks(self, active_ids: set):
        for tid in list(self.history):
            if tid in active_ids:
                continue
            self.missed[tid] = self.missed.get(tid, 0) + 1
            if self.missed[tid] > self.grace:
                self.history.pop(tid, None)
                self.missed.pop(tid, None)

    def reset(self):
        """Wywołaj przy zmianie wideo / trackera."""
        self.history.clear()
        self.missed.clear()