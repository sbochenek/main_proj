# app/backend\visualization\video.py
from ultralytics import YOLO
from PyQt5.QtCore import QThread, pyqtSignal

import subprocess
import cv2
import numpy as np
import threading

class Video(QThread):

    frame_ready = pyqtSignal(object)
    error_occurred = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.width = 1280
        self.height = 900

        self.source = None
        self.cap = None

        self._is_running = True

        # Synchronizacja Video z FrameProcessor
        self._frame_processed = threading.Event()

        # Początkowo Video nie musi czekać
        self._frame_processed.set()

    def resize_video_to_dimensions(self, width: int, height: int) -> None:
        self.width = width
        self.height = height

    def change_video_source(self, source):
        if self.isRunning():
            self.stop()

        self.source = source
        return True
    
    def run(self):

        if self.source is None:
            self.error_occurred.emit("Nie wybrano źródła wideo")
            return

        self._is_running = True

        try:
            # Otwarcie źródła w wątku Video
            self.cap = cv2.VideoCapture(self.source)

            if not self.cap.isOpened():
                self.error_occurred.emit(
                    f"Nie można otworzyć źródła: {self.source}"
                )
                return

            while self._is_running:

                ret, frame = self.cap.read()

                if not ret:
                    break

                # Dopasowanie rozmiaru obrazu
                frame = cv2.resize(
                    frame,
                    (self.width, self.height)
                )

                # Przygotowanie oczekiwania na zakończenie
                # przetwarzania aktualnej klatki
                self._frame_processed.clear()

                # Przekazanie surowej klatki
                self.frame_ready.emit(frame)

                # Oczekiwanie na zakończenie analizy
                while self._is_running:

                    if self._frame_processed.wait(timeout=0.1):
                        break

        except Exception as exc:
            self.error_occurred.emit(str(exc))

        finally:
            self._is_running = False

            if self.cap is not None:
                self.cap.release()
                self.cap = None

    def processing_finished(self):
        """
        Wywoływane po zakończeniu analizy klatki.
        Event.set() jest bezpieczne do wywołania z innego wątku.
        """
        self._frame_processed.set()

    def stop(self):

        self._is_running = False

        # Odblokowanie Video, jeżeli oczekuje na przetworzenie
        self._frame_processed.set()

        if self.isRunning():
            self.wait()



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


def test_video():

    video = Video()
    video.stream_source = 'https://s1.worldcam.live:8082/aleksandrow-lodzki-dmowskiego-konstantynowska/tracks-v1/mono.ts.m3u8?token=767db5b2946c512c82598f36e7cecd1755b417ab69b7629d1ab73e1a0bbf7f89'
    width, height = 1920, 1080

    # Komenda FFmpeg wypuszczająca surowe klatki w formacie BGR24 na standardowe wyjście (pipe)
    ffmpeg_cmd = [
        "ffmpeg",
        "-i",
        video.stream_source,
        "-f",
        "image2pipe",
        "-pix_fmt",
        "bgr24",
        "-vcodec",
        "rawvideo",
        "-",
    ]

    # Uruchomienie procesu FFmpeg
    pipe = subprocess.Popen(
        ffmpeg_cmd,
        stdout=subprocess.PIPE,
        stderr=None,  # ukrywa logi FFmpeg, zmień na None jeśli chcesz debugować
        bufsize=10**8,
    )

    frame_size = width * height * 3

    print("Otwieranie strumienia przez FFmpeg...")

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

if __name__ == "__main__":    
    test_video()