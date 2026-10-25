# models.py
import os
from enum import Enum

import cv2

from ultralytics import YOLO
import supervision as sv
from trackers import ByteTrackTracker

root = os.getcwd()
models_det_dir_park_slot = os.path.join(root, "models\\park_det_models")
models_det_dir_car = os.path.join(root, "models\\car_det_models")
models_dir = os.path.join(root, "models")


vehicle_classes = [2, 3, 5, 7]

class ModelType(Enum):
    DET_PARK_SPOT = "park_spot_det"
    DET_CAR = "car_det"
    TRACKING = "tracking"

class Models():
    def __init__(self):
        self.active_models = {
            ModelType.DET_PARK_SPOT: None,
            ModelType.DET_CAR: None,
            ModelType.TRACKING: None
        }
        self.models_det_park_spot = []
        self.loaded_model_det_park_spot = None
        self.model_det_park_spot_conf = 0.25

        self.models_det_cars = []
        self.loaded_model_det_cars = None
        self.model_det_park_cars_conf = 0.25

        self.is_tracking_enabled = True
        self.tracker = ByteTrackTracker(
            track_activation_threshold=0.25,
            minimum_consecutive_frames=1
            )
            
           
        self.box_annotator = sv.BoxAnnotator()
        self.label_annotator = sv.LabelAnnotator()
        self.trace_annotator = sv.TraceAnnotator()
        # wczytywanie modeli
        self.load_models_from_dir(models_det_dir_park_slot, self.models_det_park_spot)
        self.load_models_from_dir(models_det_dir_car, self.models_det_cars)


    def load_models_from_dir(self, directory: str, target_list: list):
        """metoda do wczytywania plików .pt z wskazanego katalogu."""
        if not os.path.exists(directory):
            return  # Zabezpieczenie, gdyby katalog jeszcze nie istniał
            
        for file_name in os.listdir(directory):
            if file_name.endswith('.pt'):
                target_list.append(file_name)
        print(f"wczytane pliki: {target_list}")


    def set_active_model(self, model_type: str, model_name: str):
        """Zapisuje model w odpowiedniej kategorii"""
        if model_type in self.active_models:
            self.active_models[model_type] = model_name
            print(f"Backend -> Zaktualizowano [{model_type.value}] na model: {model_name}")

            if model_type == ModelType.DET_PARK_SPOT:
                self.loaded_model_det_park_spot = YOLO(os.path.join(models_det_dir_park_slot, model_name))
            elif model_type == ModelType.DET_CAR:
                self.loaded_model_det_cars = YOLO(os.path.join(models_det_dir_car, model_name))
            else:
                print(f"blad wczytywanie modelu po znalezionym typie typ: {model_type}")
                return
        else:
            print(f"Błąd: Nieznany typ modelu: {model_type}")
            return


    def process_frame(self, frame):
        if self.loaded_model_det_park_spot is not None:
            frame = self.check_parking_slots(frame)

        if self.loaded_model_det_cars is not None:
            frame = self.detect_cars(frame)

        # if self.loaded_model_det_cars is not None and self.loaded_model_track_cars is not None:
        #     frame = self.track_cars(frame)

        return frame


    def check_parking_slots(self, frame):
        results = self.loaded_model_det_park_spot(frame, conf=self.model_det_park_spot_conf, verbose=False)[0]

        # Rysowanie bounding boxów
        for box in results.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cls = int(box.cls[0])
            label = self.loaded_model_det_park_spot.names[cls]
            conf_val = float(box.conf[0])
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(
                frame, f"{label} {conf_val:.2f}",
                (x1, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2
            )
        return frame


    def detect_cars(self, frame):
        if self.loaded_model_det_cars == 'yolo26m.pt':
            results = self.model(
            frame, 
            conf=self.model_det_park_cars_conf, 
            classes=vehicle_classes,  # <-- wykrycia tylko do pojazdów
            verbose=False)[0]
        else: 
            results = self.loaded_model_det_cars(frame, conf=0.25, verbose=False)[0]


        if self.is_tracking_enabled:
            frame = self.track_cars(frame, results)
            return frame
        else:
            for box in results.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cls = int(box.cls[0])
                label = self.loaded_model_det_cars.names[cls]
                conf_val = float(box.conf[0])
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(
                    frame, f"{label} {conf_val:.2f}",
                    (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2
                )
            return frame

    def track_cars(self, frame, result):
        detections = sv.Detections.from_ultralytics(result)

        # 3. Przypisanie identyfikatorów przez ByteTrack
        detections = self.tracker.update(detections)

        # 4. Pominięcie obiektów bez przypisanego ID
        detections = detections[detections.tracker_id != -1]

        # 5. Przygotowanie etykiet: ID + nazwa klasy
        labels = [
            f"ID {tracker_id} {result.names[class_id]}"
            for tracker_id, class_id in zip(
                detections.tracker_id,
                detections.class_id
            )
        ]

        # 6. Rysowanie wyników
        annotated_frame = self.box_annotator.annotate(
            scene=frame.copy(),
            detections=detections
        )

        annotated_frame = self.label_annotator.annotate(
            scene=annotated_frame,
            detections=detections,
            labels=labels
        )

        annotated_frame = self.trace_annotator.annotate(
            scene=annotated_frame,
            detections=detections
        )
        return annotated_frame




class Tracking_algorithms():
    def __init__(self):
        self.bytetrack