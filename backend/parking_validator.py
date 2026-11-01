
import numpy as np
import supervision as sv

class ParkingValidator:

    def __init__(
        self,
        overlap_threshold=0.4,
        movement_threshold=5.0
    ):
        self.overlap_threshold = overlap_threshold
        self.movement_threshold = movement_threshold

        # Historia położenia pojazdów
        self.previous_centers = {}

        # Czy pojazd kiedykolwiek się przemieścił
        self.has_moved = {}

    @staticmethod
    def calculate_coverage(car_box, parking_box):
        # print("start calculate_coverage")
        cx1, cy1, cx2, cy2 = car_box
        px1, py1, px2, py2 = parking_box[0]
        
        # Część wspólna boxów
        ix1 = max(cx1, px1)
        iy1 = max(cy1, py1)
        ix2 = min(cx2, px2)
        iy2 = min(cy2, py2)

        intersection = (
            max(0, ix2 - ix1) *
            max(0, iy2 - iy1)
        )

        car_area = max(0, cx2 - cx1) * max(0, cy2 - cy1)

        if car_area == 0:
            return 0.0

        # print("koniec calculate_coverage")
        return intersection / car_area

    def check_parking_overlap(self, car_box, parking_detections):

        # print(f'poczatek check_parking_overlap')
        if len(parking_detections) > 0:
            for parking_box in parking_detections:
                # print(f'start petli w check_parking_overlap')
                coverage = self.calculate_coverage(
                    car_box,
                    parking_box
                )
                if coverage >= self.overlap_threshold:
                    # print(f'koniec check_parking_overlap')
                    return True
            return False
        # print(f'koniec check_parking_overlap')
        return False

    def check_movement(self, track_id, car_box):
        # print("poczatek check_movement")
        if track_id is None:
            return False

        x1, y1, x2, y2 = car_box

        center = np.array([
            (x1 + x2) / 2,
            (y1 + y2) / 2
        ])

        moved = False

        if track_id in self.previous_centers:

            previous = self.previous_centers[track_id]

            distance = np.linalg.norm(center - previous)

            if distance >= self.movement_threshold:
                moved = True
                self.has_moved[track_id] = True

        else:
            self.has_moved[track_id] = False

        self.previous_centers[track_id] = center
        # print("koniec check_movement")
        return moved

    def validate(self, car_detections, parking_detections, tracking_enabled):
        # labels [ID ] detections.tracker_id detections.class_id
        # car_detections & parking_detections = YOlO results
        car_dets = sv.Detections.from_ultralytics(car_detections)
        park_dets = sv.Detections.from_ultralytics(parking_detections)
        labels = []
        # print(f'poczatek validate')
        if len(car_dets) > 0:
            for i, car_box in enumerate(car_dets.xyxy):

                # 1. Czy samochód nachodzi na miejsce parkingowe?
                overlap = self.check_parking_overlap(
                    car_box,
                    park_dets
                )

                # 2. Sprawdzenie przemieszczenia
                track_id = None


                # print("validate przed pierwszym warunkiem")
                if tracking_enabled and len(car_dets) > 0:
                    track_id = int(car_dets.tracker_id[i])

                # print("validate przed drugim warunkiem")
                if tracking_enabled:
                    self.check_movement(track_id, car_box)

                moved = (
                    self.has_moved.get(track_id, False)
                    if tracking_enabled and track_id is not None
                    else False
                )

                # 3. Decyzja
                if overlap:
                    status = "Poprawne parkowanie"
                elif moved:
                    status = "W ruchu"
                else:
                    status = "Niepoprawne parkowanie"

                if tracking_enabled and track_id is not None and track_id != -1:
                    combined_label = f"ID {track_id}: {status}"
                else:
                    combined_label = f"{status}"

                # Dodanie do głównej listy etykiet
                labels.append(combined_label)
                
        # print("koniec validate")
        return car_dets, labels
