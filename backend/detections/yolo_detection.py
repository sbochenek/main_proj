# main_app\backend\detections\yolo_detection.py

print('[YOLO DETECTIONS] start')
import os
import numpy as np
from ultralytics import YOLO
from .models_type import ModelType

root = os.getcwd()
models_det_dir_park_slot = os.path.join(root, "models\\yolo_models\\park_det_models")
models_det_dir_car = os.path.join(root, "models\\yolo_models\\car_det_models")


# Klasy wybierane po NAZWACH z model.names, a nie po numerach ID –
# dzięki temu ten sam kod działa dla modeli o różnych zestawach klas:
#   yolo26m (COCO):            2 car, 3 motorcycle, 5 bus, 7 truck, 0 person
#   yolov10_vehicle_detection: 0 bus, 1 car, 2 motorcycle, 4 truck, 3 pedestrian
VEHICLE_CLASS_NAMES = {
    "car", "truck", "bus", "motorcycle", "motorbike",
    "van", "vehicle", "pickup", "minivan", "suv",
}
PEDESTRIAN_CLASS_NAMES = {"person", "pedestrian", "people"}


print("[MODELS] Importy zakończone, definiuję klasę Models", flush=True)
class YOLODetection():
    def __init__(self):
        self.active_models = {
            ModelType.DET_PARK_SPOT: None,
            ModelType.DET_CAR: None,
        }
        self.det_park_list = []
        self.park_det_loaded = None
        self.park_conf = 0.4

        self.det_cars_list = []
        self.car_det_loaded = None
        self.car_conf = 0.4

        # Filtrowanie klas modelu detekcji pojazdów
        self.detect_pedestrians = False       # opcjonalne wykrywanie pieszych
        self.vehicle_class_ids = frozenset()  # ID klas pojazdów aktywnego modelu
        self.pedestrian_class_ids = frozenset()
        self._car_classes = None              # lista ID przekazywana do YOLO (classes=)

        self.load_models_from_dir(models_det_dir_park_slot, self.det_park_list)
        self.load_models_from_dir(models_det_dir_car, self.det_cars_list)

    def load_models_from_dir(self, directory: str, target_list: list):
        """metoda do wczytywania plików .pt z wskazanego katalogu."""
        if not os.path.exists(directory):
            return  # Zabezpieczenie, gdyby katalog jeszcze nie istniał

        for file_name in os.listdir(directory):
            if file_name.endswith('.pt'):
                target_list.append(file_name)
        print(f"wczytane pliki: {target_list}")


    # ---------- filtrowanie klas ----------
    def _update_car_classes(self, model=None):
        """Wyznacza ID klas pojazdów i pieszych dla aktywnego modelu pojazdów."""
        model = model if model is not None else self.car_det_loaded
        if model is None:
            self.vehicle_class_ids = frozenset()
            self.pedestrian_class_ids = frozenset()
            self._car_classes = None
            return

        names = model.names  # dict {id: nazwa}
        vehicles = {i for i, n in names.items() if str(n).lower() in VEHICLE_CLASS_NAMES}
        pedestrians = {i for i, n in names.items() if str(n).lower() in PEDESTRIAN_CLASS_NAMES}

        if not vehicles:
            # model o nieznanych nazwach klas: wszystko poza pieszymi traktujemy jako pojazdy
            vehicles = set(names) - pedestrians
            print(f"[YOLO] Uwaga: brak znanych nazw klas pojazdów w {names}; "
                  f"przyjęto wszystkie klasy poza pieszymi.")

        selected = vehicles | pedestrians if self.detect_pedestrians else vehicles

        # przypisania pojedynczymi referencjami – bezpieczne przy odczycie z wątku przetwarzania
        self.vehicle_class_ids = frozenset(vehicles)
        self.pedestrian_class_ids = frozenset(pedestrians)
        self._car_classes = sorted(selected)

        print(f"[YOLO] pojazdy: {[names[i] for i in sorted(vehicles)]}, "
              f"piesi: {[names[i] for i in sorted(pedestrians)] if self.detect_pedestrians else 'wyłączeni'}")

    def set_detect_pedestrians(self, enabled: bool):
        self.detect_pedestrians = bool(enabled)
        self._update_car_classes()

    def vehicle_mask(self, class_ids) -> np.ndarray:
        """Maska bool: True dla detekcji, które są pojazdami (np. do walidacji parkowania)."""
        if class_ids is None:
            return np.zeros(0, dtype=bool)
        return np.isin(np.asarray(class_ids), list(self.vehicle_class_ids))


    def set_active_model(self, model_type: str, model_name: str):
        """wlacza model w odpowiedniej kategorii"""

        if model_type not in self.active_models:
            print(f"Błąd: Nieznany typ modelu: {model_type}")
            return False

        # Ponowne kliknięcie aktywnego modelu
        if self.active_models[model_type] == model_name:
            self.deactivate_model(model_type)
            return True

        if model_type == ModelType.DET_PARK_SPOT:
            model_path = os.path.join(models_det_dir_park_slot, model_name)
        elif model_type == ModelType.DET_CAR:
            model_path = os.path.join(models_det_dir_car, model_name)
        else:
            return False

        try:
            new_model = YOLO(model_path)

        except Exception as e:
            print(f"Błąd wczytywania modelu {model_name}: {e}")
            return False

        # Aktualizacja stanu dopiero po udanym wczytaniu
        if model_type == ModelType.DET_PARK_SPOT:
            self.park_det_loaded = new_model
        elif model_type == ModelType.DET_CAR:
            # najpierw klasy, potem model – wątek przetwarzania nie dostanie
            # nowego modelu ze starą listą klas
            self._update_car_classes(new_model)
            self.car_det_loaded = new_model

        self.active_models[model_type] = model_name

        print(
            f"Backend -> Zaktualizowano {model_type}"
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
            self.park_det_loaded = None
            print("Wyłączanie detekcji parkingów")

        elif model_type == ModelType.DET_CAR:
            self.car_det_loaded = None
            self._update_car_classes()
            print("Wyłączanie detekcji pojazdów")

        return True


    def detect_park_slot(self, frame):
        if self.park_det_loaded is not None:
            results = self.park_det_loaded(frame, conf=self.park_conf, verbose=False)[0]
            return results
        else:
            return None

    def detect_cars(self, frame):
        model = self.car_det_loaded
        classes = self._car_classes
        if model is not None:
            # classes= -> YOLO zwraca tylko pojazdy (i ewentualnie pieszych)
            results = model(frame, conf=self.car_conf, classes=classes, verbose=False)[0]
            return results
        else:
            return None

    def change_cars_thr(self, value):
        print(f"zmiana thr w detekcji pojazdow na: {value}")
        self.car_conf = value

    def change_park_thr(self, value):
        print(f"zmiana thr w detekcji miejsc parkingowych na: {value}")
        self.park_conf = value

print('[YOLO DETECTIONS] ok')