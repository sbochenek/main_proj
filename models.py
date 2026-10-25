# models.py
import os
from enum import Enum

import cv2

from ultralytics import YOLO


root = os.getcwd()
models_det_dir_park_slot = os.path.join(root, "models\\park_det_models")
models_dir = os.path.join(root, "models")

class ModelType(Enum):
    DET_PARK_SPOT = "park_spot_det"
    PARKING = "parking"
    TRACKING = "tracking"

class Models():
    def __init__(self):
        self.active_models = {
            ModelType.DET_PARK_SPOT: None,
            "parking": None,
            "tracking": None
        }
        self.models_det_park_spot = []
        self.loaded_model_det_park_spot = None
        self.models_det_cars = []
        self.loaded_model_det_cars = None
        self.det_models = []
        self.track_models = []
        self.load_det_models()
        self.load_models_from_dir(models_det_dir_park_slot, self.models_det_park_spot)


    def load_models_from_dir(self, directory: str, target_list: list):
        """Uniwersalna metoda do wczytywania plików .pt z wskazanego katalogu."""
        if not os.path.exists(directory):
            return  # Zabezpieczenie, gdyby katalog jeszcze nie istniał
            
        for file_name in os.listdir(directory):
            if file_name.endswith('.pt'):
                target_list.append(file_name)

    def load_det_models(self):
        models = os.listdir(models_dir)
        for model in models:
            if model.endswith('.pt'):
                self.det_models.append(model)

    def set_active_model(self, model_type: str, model_name: str):
        """Zapisuje model w odpowiedniej kategorii"""
        if model_type in self.active_models:
            self.active_models[model_type] = model_name
            print(f"Backend -> Zaktualizowano [{model_type.value}] na model: {model_name}")

            if model_type == ModelType.DET_PARK_SPOT:
                self.loaded_model_det_park_spot = YOLO(os.path.join(models_det_dir_park_slot, model_name))
            elif model_type == ModelType.PARKING:
                print('tmp')
            else:
                print("brak typu")
                return
        else:
            print(f"Błąd: Nieznany typ modelu: {model_type}")
            return


    def process_frame(self, frame):
        if self.loaded_model_det_park_spot is None:
            return frame
        
        processed_frame = self.check_parking_slots(frame)
        return processed_frame


    def check_parking_slots(self, frame):
        conf = 70 / 100.0
        results = self.loaded_model_det_park_spot(frame, conf=conf, verbose=False)[0]

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