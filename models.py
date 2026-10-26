# models.py
import os
from enum import Enum

import onnxruntime as ort
print("ONNX Runtime:", ort.__version__)

import cv2
print("OpenCV OK")

from ultralytics import YOLO
print("Ultralytics OK")

import supervision as sv
print("Supervision OK")

from trackers import (
    ByteTrackTracker,
    BoTSORTTracker,
    OCSORTTracker,
    SORTTracker,
)
print("Trackers OK")

from inference import get_model
print("Inference OK")
print("[MODELS] Początek inicjalizacji", flush=True)

root = os.getcwd()
models_det_dir_park_slot = os.path.join(root, "models\\park_det_models")
models_det_dir_car = os.path.join(root, "models\\car_det_models")
models_dir = os.path.join(root, "models")


vehicle_classes = [2, 3, 5, 7]

class ModelType(Enum):
    DET_PARK_SPOT = "park_spot_det"
    DET_CAR = "car_det"

class TrackerAlg(Enum):
    SORTTracker = "SORTTracker"
    OCSORTTracker = "OCSORTTracker"
    BoTSORTTracker = "BoTSORTTracker"
    ByteTrack = "ByteTrack"

print("[MODELS] Importy zakończone, definiuję klasę Models", flush=True)
class Models():
    def __init__(self):
        self.active_models = {
            ModelType.DET_PARK_SPOT: None,
            ModelType.DET_CAR: None,
        }
        self.models_det_park_spot = []
        self.loaded_model_det_park_spot = None
        self.model_det_park_spot_conf = 0.25

        self.models_det_cars = []
        self.loaded_model_det_cars = None
        self.model_det_cars_conf = 0.25

        self.trackers = TrackerAlg
        self.trackers_algs = Tracking_algorithms()
        self.loaded_tracker = None
        self.is_tracking_enabled = False
            
           
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
        results = None
        if self.loaded_model_det_park_spot is not None:
            frame = self.check_parking_slots(frame)

        if self.loaded_model_det_cars is not None:
            frame, results = self.detect_cars(frame)
            if self.loaded_model_det_cars is not None and self.loaded_tracker is not None:
                frame = self.track_cars(frame, results)

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
            results = self.loaded_model_det_cars(
            frame, 
            conf=self.model_det_cars_conf, 
            classes=vehicle_classes,  # <-- wykrycia tylko do pojazdów
            verbose=False)[0]
        else: 
            results = self.loaded_model_det_cars(frame, conf=self.model_det_cars_conf, verbose=False)[0]


        if not self.is_tracking_enabled:
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
        return frame, results

    def change_cars_thr(self, value):
        self.model_det_cars_conf = value

    def change_park_thr(self, value):
        self.model_det_park_spot_conf = value



    def track_cars(self, frame, result):
        detections = sv.Detections.from_ultralytics(result)

        # 3. Przypisanie identyfikatorów przez ByteTrack
        detections = self.loaded_tracker.update(detections)

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

    def set_track_alg(self, algtype):
        self.reset_track_alg()
        self.is_tracking_enabled = True
        if algtype == TrackerAlg.ByteTrack.value:
            self.loaded_tracker = self.trackers_algs.ByteTrack
        elif algtype == TrackerAlg.BoTSORTTracker.value:
            self.loaded_tracker = self.trackers_algs.BoTSORTTracker
        elif algtype == TrackerAlg.OCSORTTracker.value:
            self.loaded_tracker = self.trackers_algs.OCSORTTracker
        elif algtype == TrackerAlg.SORTTracker.value:
            self.loaded_tracker = self.trackers_algs.SORTTracker
        else:
            self.loaded_tracker = None
            print(f'nieznany typ trackera {algtype}')
            self.is_tracking_enabled = False
        print(f"ustawiono tracker {self.loaded_tracker.__class__.__name__} tacking enabled? {self.is_tracking_enabled}")

    def reset_track_alg(self):
        if self.loaded_tracker is not None:
            self.loaded_tracker.reset()
            print("zresetowano dane trackera")
        self.loaded_tracker = None
        self.is_tracking_enabled = False



class Tracking_algorithms():
    def __init__(self):
        self.ByteTrack = ByteTrackTracker(
            lost_track_buffer=30,
            frame_rate=30.0, #todo  przetwarzanie z pomijaniem klatek
            track_activation_threshold=0.7, # pewnosc przy inicjowaniu nowych sladow
            minimum_consecutive_frames=2,   # liczba klatek zanim otrzyma id
            minimum_iou_threshold=0.1,
            high_conf_det_threshold=0.6,
            # state_estimator_class=XYXYStateEstimator,
            # iou=None
        )

        self.BoTSORTTracker = BoTSORTTracker(
            lost_track_buffer=30,
            frame_rate=30.0,
            track_activation_threshold=0.7,
            minimum_consecutive_frames=2,
            minimum_iou_threshold_first_assoc=0.2,
            minimum_iou_threshold_second_assoc=0.5,
            minimum_iou_threshold_unconfirmed_assoc=0.3,
            high_conf_det_threshold=0.6,
            enable_cmc=True, # kompensacja ruchu kamery
            cmc_method="sparseOptFlow", # "sift" "sparseOptFlow" "ecc"
            cmc_downscale=2,
            instant_first_frame_activation=True,
            # state_estimator_class=XCYCWHStateEstimator,
            # iou=None
        )

        self.OCSORTTracker = OCSORTTracker(
            lost_track_buffer=30,
            frame_rate=30.0,
            minimum_consecutive_frames=3,
            minimum_iou_threshold=0.3,
            direction_consistency_weight=0.2,
            high_conf_det_threshold=0.6,
            delta_t=3,
            # state_estimator_class=XCYCSRStateEstimator,
            # iou=None
        )
        
        self.SORTTracker = SORTTracker(
            lost_track_buffer=30,
            frame_rate=30.0,
            track_activation_threshold=0.25,
            minimum_consecutive_frames=3,
            minimum_iou_threshold=0.3,
            # state_estimator_class=XYXYStateEstimator,
            # iou=None
        )



def main():
    # a = Tracking_algorithms()
    print(help(SORTTracker))

if __name__ == "__main__":

    main()
