# ./backend.py
from PyQt5.QtCore import QObject, pyqtSignal, QThread
from ultralytics import YOLO
import os
import subprocess
import cv2
import numpy as np


class Video(QThread):
    frame_ready = pyqtSignal(np.ndarray)

    def __init__(self):
        super().__init__()
        self.width = 1280
        self.height = 900
        self.source = None
        self.cap = None
        self._is_running = True


        self.frame_size = self.width * self.height * 3

    def resize_video_to_dimensions(self, width: int, height: int) -> None:
        """zmiana rozmiarow klatki na odpowiadajace rozmiarowi ekranu video"""
        self.width = width
        self.height = height

    def change_video_source(self, source):
        """zmiana zrodla video z wylaczeniem poprzedniego streamu"""
        if self.cap and self.cap.isOpened():
            self.cap.release()

        self.cap = cv2.VideoCapture(source)
        
        if not self.cap.isOpened():
            print("Błąd: Nie udało się otworzyć strumienia M3U8!")

    def run(self):
        # Pętla odczytująca klatki w wątku
        self._is_running = True
        while self._is_running:
            if self.cap and self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret:
                    self.frame_ready.emit(frame)
                else:
                    print("Utracono klatkę / koniec strumienia.")
                    break

    def stop(self):
        self._is_running = False
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