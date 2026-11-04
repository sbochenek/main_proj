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


