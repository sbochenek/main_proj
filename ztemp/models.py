# models.py
import os
from enum import Enum

from ultralytics.trackers.utils.kalman_filter import KalmanFilterXYAH
import numpy as np

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

#from inference import get_model
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
            
        self.predictors = {'pred1, pred2'}

        self.box_annotator = sv.BoxAnnotator()
        self.label_annotator = sv.LabelAnnotator()
        self.trace_annotator = sv.TraceAnnotator()
        # wczytywanie modeli
        self.load_models_from_dir(models_det_dir_park_slot, self.models_det_park_spot)
        self.load_models_from_dir(models_det_dir_car, self.models_det_cars)

        self.prediction_object = Predictions()

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

        if model_type not in self.active_models:
            print(f"Błąd: Nieznany typ modelu: {model_type}")
            return False

        if not model_name:
            print("Błąd: Nie podano nazwy modelu.")
            return False

        # Ponowne kliknięcie aktywnego modelu
        if self.active_models[model_type] == model_name:
            self.deactivate_model(model_type)
            return True
        
        if model_type == ModelType.DET_PARK_SPOT:
            model_path = os.path.join(
                models_det_dir_park_slot,
                model_name
            )

        elif model_type == ModelType.DET_CAR:
            model_path = os.path.join(
                models_det_dir_car,
                model_name
            )
        else:
            return False
        
        try:
            new_model = YOLO(model_path)

        except Exception as e:
            print(f"Błąd wczytywania modelu {model_name}: {e}")
            return False

        # Aktualizacja stanu dopiero po udanym wczytaniu
        if model_type == ModelType.DET_PARK_SPOT:
            self.loaded_model_det_park_spot = new_model

        elif model_type == ModelType.DET_CAR:
            self.loaded_model_det_cars = new_model

        self.active_models[model_type] = model_name

        print(
            f"Backend -> Zaktualizowano "
            f"[{model_type.value}] na model: {model_name}"
        )

        return True


    def deactivate_model(self, model_type: ModelType):
        """Wyłącza detektor określonego typu."""

        if model_type not in self.active_models:
            print(f"Błąd: Nieznany typ modelu: {model_type}")
            return False

        self.active_models[model_type] = None

        if model_type == ModelType.DET_PARK_SPOT:
            self.loaded_model_det_park_spot = None
            print("Wyłączanie detekcji parkingów")

        elif model_type == ModelType.DET_CAR:
            self.loaded_model_det_cars = None
            print("Wyłączanie detekcji pojazdów")

        return True

    def process_frame(self, frame):
        results = None
        if self.loaded_model_det_park_spot is not None:
            frame = self.check_parking_slots(frame)

        if self.loaded_model_det_cars is not None:
            frame, results = self.detect_cars(frame)
            if self.loaded_model_det_cars is not None and self.loaded_tracker is not None:
                # frame = self.track_cars(frame, results)
                frame = self.prediction_object.pred(frame, results)
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
            print('rysowaine boxow bez trackera')
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
        print(f"zmiana thr w detekcji pojazdow na: {value}")
        self.model_det_cars_conf = value

    def change_park_thr(self, value):
        print(f"zmiana thr w detekcji miejsc parkingowych na: {value}")
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

        if self.loaded_tracker.__class__.__name__ == algtype:
            self.reset_track_alg()
            self.is_tracking_enabled = False
            self.loaded_tracker = None
            print(f"wylaczanie funkcji sledzenia")
            return

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


class Predictions():
    def __init__(self):
        self.kf = KalmanFilterXYAH()
        self.next_track_id = 0
        self.tracks = {}
        self.box_annotator = sv.BoxAnnotator()
        self.label_annotator = sv.LabelAnnotator()
        self.trace_annotator = sv.TraceAnnotator()
    def pred(self, frame, results):
            print('wywolanie funkcji pred')
            
            detections_list = []

            # 1. Predykcja Kalmana dla wszystkich istniejących śladów
            for track_id, track in self.tracks.items():
                track["mean"], track["covariance"] = self.kf.predict(
                    track["mean"], track["covariance"]
                )

            # 2. Odczyt detekcji z YOLO dla bieżącej klatki i budowanie pomiarów dla Kalmana
            yolo_detections = []
            if results.boxes is not None and len(results.boxes) > 0:
                boxes = results.boxes.xyxy.cpu().numpy()
                classes = results.boxes.cls.cpu().numpy()
                confidences = results.boxes.conf.cpu().numpy()
                
                for box, cls, conf in zip(boxes, classes, confidences):
                    x1, y1, x2, y2 = box
                    w = x2 - x1
                    h = y2 - y1
                    x_center = x1 + w / 2.0
                    y_center = y1 + h / 2.0
                    aspect_ratio = w / float(h) if h > 0 else 0

                    measurement = np.array([x_center, y_center, aspect_ratio, h])
                    yolo_detections.append({
                        "measurement": measurement,
                        "cls": int(cls),
                        "conf": float(conf)
                    })

            # 3. Asocjacja i aktualizacja filtrów Kalmana
            assigned_track_ids = set()
            
            # Listy do zbudowania sv.Detections dla Supervision
            xyxy_list = []
            tracker_id_list = []
            confidence_list = []
            class_id_list = []

            for item in yolo_detections:
                det = item["measurement"]
                matched_id = None
                min_dist = float("inf")
                
                for track_id, track in self.tracks.items():
                    if track_id in assigned_track_ids:
                        continue
                    
                    dist = np.linalg.norm(track["mean"][:2] - det[:2])
                    if dist < 50.0 and dist < min_dist:
                        min_dist = dist
                        matched_id = track_id

                if matched_id is not None:
                    # Aktualizacja istniejącego śladu
                    self.tracks[matched_id]["mean"], self.tracks[matched_id]["covariance"] = self.kf.update(
                        self.tracks[matched_id]["mean"], self.tracks[matched_id]["covariance"], det
                    )
                    assigned_track_ids.add(matched_id)
                    current_id = matched_id
                    track_to_draw = self.tracks[matched_id]["mean"]
                else:
                    # Inicjalizacja nowego śladu
                    mean, covariance = self.kf.initiate(det)
                    self.tracks[self.next_track_id] = {"mean": mean, "covariance": covariance}
                    current_id = self.next_track_id
                    track_to_draw = mean
                    assigned_track_ids.add(self.next_track_id)
                    self.next_track_id += 1

                # Obliczenie współrzędnych xyxy z uaktualnionego stanu Kalmana
                x, y, a, h = track_to_draw[:4]
                w = a * h
                x1 = int(x - w / 2)
                y1 = int(y - h / 2)
                x2 = int(x + w / 2)
                y2 = int(y + h / 2)

                xyxy_list.append([x1, y1, x2, y2])
                tracker_id_list.append(current_id)
                confidence_list.append(item["conf"])
                class_id_list.append(item["cls"])

            # 4. Jeśli mamy ślady, tworzymy obiekt sv.Detections i rysujemy adnotatorami
            if len(xyxy_list) > 0:
                detections = sv.Detections(
                    xyxy=np.array(xyxy_list, dtype=np.float32),
                    confidence=np.array(confidence_list, dtype=np.float32),
                    class_id=np.array(class_id_list, dtype=int),
                    tracker_id=np.array(tracker_id_list, dtype=int)
                )

                # Przygotowanie etykiet (ID + nazwa klasy z modelu YOLO)
                labels = [
                    f"ID {tid} {results.names[cid]}"
                    for tid, cid in zip(detections.tracker_id, detections.class_id)
                ]

                # Rysowanie za pomocą Supervision Annotators
                annotated_frame = frame.copy()
                annotated_frame = self.box_annotator.annotate(scene=annotated_frame, detections=detections)
                annotated_frame = self.label_annotator.annotate(scene=annotated_frame, detections=detections, labels=labels)
                annotated_frame = self.trace_annotator.annotate(scene=annotated_frame, detections=detections)

                for tid in tracker_id_list:
                    if tid in self.tracks:
                        # Pobieramy np. 15 klatek w przód
                        future_steps = self.predict_future(tid, future_frames=20)
                        
                        points = []
                        for step in future_steps:
                            # Przeliczamy środki przewidywanych prostokątów na punkty na ekranie
                            fx = int(step["x"])
                            fy = int(step["y"])
                            points.append((fx, fy))
                        
                        # Rysujemy linie łączące punkty przyszłej trajektorii
                        for i in range(len(points) - 1):
                            cv2.line(annotated_frame, points[i], points[i+1], (0, 255, 255), 2)  # Żółta linia
                            cv2.circle(annotated_frame, points[i+1], 3, (0, 0, 255), -1)        # Czerwone kropki

                return annotated_frame
                
            return frame

    def predict_future(self, track_id, future_frames=10):

        track = self.tracks[track_id]

        mean = track["mean"].copy()
        covariance = track["covariance"].copy()

        predictions = []

        for i in range(future_frames):

            mean, covariance = self.kf.predict(
                mean, covariance
            )

            x, y, a, h = mean[:4]

            w = a * h

            predictions.append({
                "frame": i + 1,
                "x": x,
                "y": y,
                "width": w,
                "height": h
            })

        return predictions

def main():
    # a = Tracking_algorithms()
    print(help(SORTTracker))

if __name__ == "__main__":

    main()
