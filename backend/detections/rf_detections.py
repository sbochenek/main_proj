# main_app\backend\detections\rf_detection.py

print('[rf_det] start')
import os
import supervision as sv
from .models_type import ModelType
from inference import get_model
from .rf_api_key import API
from rfdetr import RFDETRNano
print('[rf_det] Inference OK')

root = os.getcwd()
models_det_dir_park_slot = os.path.join(root, "models\\rf_models\\park_det_models")
models_det_dir_car = os.path.join(root, "models\\rf_models\\car_det_models")

    
class RFdetection():
    def __init__(self):
        self.active_models = {
          ModelType.DET_PARK_SPOT: None,
          ModelType.DET_CAR: None,
        }
        self.park_class_names = {
            1: "bump",
            2: "empty",
            3: "oku parking",
            4: "occupied",
            5: "Parking area",
            6: "Reserved parking"
        }
        self.det_park_list = []
        self.park_det_loaded = None
        self.park_conf = 0.4

        self.det_cars_list = []
        self.car_det_loaded = None
        self.car_conf = 0.4

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
            new_model = RFDETRNano(pretrain_weights=model_path)

        except Exception as e:
            print(f"Błąd wczytywania modelu {model_name}: {e}")
            return False

        # Aktualizacja stanu dopiero po udanym wczytaniu
        if model_type == ModelType.DET_PARK_SPOT:
            self.park_det_loaded = new_model
        elif model_type == ModelType.DET_CAR:
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
            print("Wyłączanie detekcji pojazdów")

        return True


    def detect_park_slot(self, frame):
        if self.park_det_loaded is not None:
            result = self.park_det_loaded.predict(frame, threshold=self.park_conf)
            return result
        else:
            return None
        
    def detect_cars(self, frame):
        if self.car_det_loaded is not None:
            result = self.car_det_loaded.predict(frame, threshold=self.car_conf)
            return result
        else: 
            return None

    def change_cars_thr(self, value):
        print(f"zmiana thr w detekcji pojazdow na: {value}")
        self.car_conf = value

    def change_park_thr(self, value):
        print(f"zmiana thr w detekcji miejsc parkingowych na: {value}")
        self.park_conf = value





print('[rf_det] ok')