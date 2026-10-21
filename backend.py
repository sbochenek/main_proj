# backend.py
from PyQt5.QtCore import QObject, pyqtSignal
from ultralytics import YOLO
import os
import subprocess
import cv2
import numpy as np

root = os.getcwd()
models_dir = os.path.join(root, "models")


class BackendManager:

  def __init__(self):
    self.video = Video()
    self.models = Models()

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

class Video():
    def __init__(self):
        self.width = 1280
        self.height = 900
        self.stream_source = ''

    def set_video_source(self, source):
        print(f"backend otrzymał video source: {source}")
        self.stream_source = source

    def load_stream(self):
        ffmpeg_cmd = [
        "ffmpeg",
        "-i",
        self.stream_source,
        "-f",
        "image2pipe",
        "-pix_fmt",
        "bgr24",
        "-vcodec",
        "rawvideo",
        "-",
        ]

        pipe = subprocess.Popen(
        ffmpeg_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,  # ukrywa logi FFmpeg, zmień na None jeśli chcesz debugować
        bufsize=10**8,
        )

        frame_size = self.width * self.height * 3

        try:
            while True:
                # Pobieramy dokładną liczbę bajtów odpowiadającą jednej klatce
                raw_frame = pipe.stdout.read(frame_size)

                if not raw_frame:
                    print("Koniec strumienia lub brak danych.")
                break

                # Konwersja surowych bajtów na tablicę NumPy
                frame = np.frombuffer(raw_frame, dtype=np.uint8).reshape(
                    (height, width, 3)
                )

                cv2.imshow("Kamera live (FFmpeg Pipe)", frame)

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
        finally:
            pipe.terminate()
            cv2.destroyAllWindows()

class Models():
    def __init__(self):
        self.det_models = []
        self.track_models = []
        self.load_det_models()

    def load_det_models(self):
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
    pass