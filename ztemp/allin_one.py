
import sys
import os
import cv2
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QFileDialog, QSlider
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap
from ultralytics import YOLO


MODELS_DIR = "models"


class VideoApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Detekcja na filmie")
        self.resize(1000, 700)

        self.cap = None
        self.model = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.next_frame)

        self._build_ui()
        self._load_models()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)

        # Pasek narzędzi
        toolbar = QHBoxLayout()

        self.btn_open = QPushButton("Otwórz film")
        self.btn_open.clicked.connect(self.open_video)
        toolbar.addWidget(self.btn_open)

        self.btn_play = QPushButton("Play")
        self.btn_play.clicked.connect(self.toggle_play)
        toolbar.addWidget(self.btn_play)

        toolbar.addWidget(QLabel("Model:"))
        self.model_combo = QComboBox()
        self.model_combo.currentTextChanged.connect(self.change_model)
        toolbar.addWidget(self.model_combo)

        toolbar.addWidget(QLabel("Próg detekcji:"))
        self.conf_slider = QSlider(Qt.Horizontal)
        self.conf_slider.setRange(10, 90)
        self.conf_slider.setValue(40)
        toolbar.addWidget(self.conf_slider)

        main_layout.addLayout(toolbar)

        # Ekran wideo
        self.video_label = QLabel("Wybierz film...")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("background:black; color:white;")
        self.video_label.setMinimumSize(800, 500)
        main_layout.addWidget(self.video_label)

    def _load_models(self):
        """Ładuje listę modeli z folderu MODELS_DIR."""
        if not os.path.isdir(MODELS_DIR):
            os.makedirs(MODELS_DIR, exist_ok=True)

        files = [f for f in os.listdir(MODELS_DIR) if f.endswith((".pt", ".onnx"))]
        self.model_combo.addItems(files)

        if files:
            self.change_model(files[0])

    def change_model(self, model_name):
        """Zmiana modelu w locie."""
        if not model_name:
            return
        path = os.path.join(MODELS_DIR, model_name)
        try:
            self.model = YOLO(path)
            print(f"Załadowano model: {model_name}")
        except Exception as e:
            print(f"Błąd ładowania modelu: {e}")

    def open_video(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Wybierz film", "", "Video (*.mp4 *.avi *.mkv *.mov)"
        )
        if not path:
            return
        if self.cap:
            self.cap.release()
        self.cap = cv2.VideoCapture(path)
        if not self.cap.isOpened():
            print("Nie można otworzyć pliku")
            return
        self.timer.start(30)  # ~30 FPS

    def toggle_play(self):
        if self.timer.isActive():
            self.timer.stop()
            self.btn_play.setText("Play")
        else:
            self.timer.start(30)
            self.btn_play.setText("Pauza")

    def next_frame(self):
        if not self.cap:
            return
        ret, frame = self.cap.read()
        if not ret:
            self.timer.stop()
            return

        # Detekcja jeśli model załadowany
        if self.model is not None:
            conf = self.conf_slider.value() / 100.0
            results = self.model(frame, conf=conf, verbose=False)[0]

            # Rysowanie bounding boxów
            for box in results.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cls = int(box.cls[0])
                label = self.model.names[cls]
                conf_val = float(box.conf[0])
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(
                    frame, f"{label} {conf_val:.2f}",
                    (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2
                )

        # Konwersja do QPixmap
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qt_img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        pix = QPixmap.fromImage(qt_img).scaled(
            self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.video_label.setPixmap(pix)

    def closeEvent(self, event):
        if self.cap:
            self.cap.release()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = VideoApp()
    win.show()
    sys.exit(app.exec_())