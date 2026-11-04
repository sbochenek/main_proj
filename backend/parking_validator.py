import numpy as np
import supervision as sv


class ParkingValidator:
    def __init__(self, overlap_threshold=0.4, movement_threshold=5.0):
        self.overlap_threshold = overlap_threshold
        self.movement_threshold = movement_threshold
        self.previous_centers: dict[int, np.ndarray] = {}
        self.has_moved: dict[int, bool] = {}

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
        if track_id is None:
            return False

        x1, y1, x2, y2 = car_box
        center = np.array([(x1 + x2) / 2, (y1 + y2) / 2])

        moved = False
        if track_id in self.previous_centers:
            distance = float(np.linalg.norm(center - self.previous_centers[track_id]))
            if distance >= self.movement_threshold:
                moved = True
                self.has_moved[track_id] = True
        else:
            self.has_moved.setdefault(track_id, False)

        self.previous_centers[track_id] = center
        return moved

    def validate(self, car_detections, parking_detections, tracking_enabled):
        """
        Zwraca (car_detections, labels) tej samej długości.
        car_detections może być None/empty -> ([], [])
        """
        if car_detections is None or len(car_detections) == 0:
            return car_detections, []

        labels: list[str] = []
        tracker_ids = car_detections.tracker_id

        for i, car_box in enumerate(car_detections.xyxy):
            # 1) overlap
            overlap = self.check_parking_overlap(car_box, parking_detections)

            # 2) track_id – bezpiecznie
            track_id = None
            if tracking_enabled and tracker_ids is not None:
                raw = tracker_ids[i]
                if raw is not None and int(raw) != -1:
                    track_id = int(raw)

            if tracking_enabled and track_id is not None:
                self.check_movement(track_id, car_box)

            moved = self.has_moved.get(track_id, False) if track_id is not None else False

            # 3) decyzja
            if overlap:
                status = "Poprawne parkowanie"
            elif moved:
                status = "W ruchu"
            else:
                status = "Niepoprawne parkowanie"

            if track_id is not None:
                labels.append(f"ID {track_id}: {status}")
            else:
                labels.append(status)

        # 4) sprzątanie osieroconych ID (opcjonalne, ale zapobiega wyciekowi)
        active_ids = {
            int(t) for t in (tracker_ids if tracker_ids is not None else [])
            if t is not None and int(t) != -1
        }
        for tid in list(self.previous_centers):
            if tid not in active_ids:
                self.previous_centers.pop(tid, None)
                self.has_moved.pop(tid, None)

        return car_detections, labels

    def reset(self):
        """Wywołaj przy zmianie wideo / resecie trackera."""
        self.previous_centers.clear()
        self.has_moved.clear()