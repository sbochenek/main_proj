# backend.py
from PyQt5.QtCore import QObject, pyqtSignal
from ultralytics import YOLO
import os

root = os.getcwd()
models_dir = os.path.join(root, "models")

class BackendModel(QObject):
    # Sygnał wysyłany do GUI, gdy dane się zmienią
    data_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._counter = 0

    def process_data(self, text_input: str):
        # Symulacja przeliczania logiki biznesowej
        self._counter += 1
        result = f"Przetworzono: '{text_input.upper()}' (Kliknięto {self._counter} razy)"
        
        # Przekazanie wyniku w świat za pomocą sygnału
        self.data_changed.emit(result)


class Models():
    def __init__(self):
        self.det_models = []
        self.track_models = []
        self.load_models()

    def load_models(self):
        models = os.listdir(models_dir)
        for model in models:
            if model.endswith('.pt'):
                self.det_models.append(model)


def main():
    model = YOLO("D:\\studia_main\\7_inzynierka\\main_app\\models\\roboflow_yolo26n_ydouj.pt")
    results = model.predict(source="D:/studia_main/7_inzynierka/modele/photos_to_test_models/test_photos/img_4.png",
                            save=True,
                            conf=0.6,

                            show_labels = True,
                            show_conf = True,
                            line_width=1,

                            project='pred_res_dir',  # Główny folder, w którym powstanie katalog
                            name='res',
                            )


def main_models():
    model = Models()
    model.load_models()
    print(model.models)


if __name__ == "__main__":    
    main_models()