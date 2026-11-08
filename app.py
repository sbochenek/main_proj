# ./app.py
import sys
print("[APP] Początek pliku", flush=True)

from inference import get_model
print("[APP] Inference OK", flush=True)

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

from gui.main_window import VideoWindowUI
from controller import AppController

from backend.visualization.video import Video
from backend.visualization.frame_process import FrameProcessor
from backend.detections.yolo_detection import YOLODetection
from backend.detections.rf_detections import RFdetection
from backend.tracking.tracking import Tracking_algorithms
from backend.predictions.predictions import Predictions
from backend.parking_validator import ParkingValidator

def main():
    app = QApplication(sys.argv)

    # 1. Inicjalizacja warstw
    view = VideoWindowUI()
    yolo_detections = YOLODetection()
    rf_detections = RFdetection()
    tracking = Tracking_algorithms()
    predictions = Predictions()
    park_validator = ParkingValidator()
    frame_processor = FrameProcessor(yolo_detections, rf_detections, tracking, predictions, park_validator)
    video = Video()
    
    controller = AppController(view, video, rf_detections, yolo_detections, tracking, predictions, frame_processor)

    app.aboutToQuit.connect(controller.shutdown)
    view.show()
    QTimer.singleShot(50, controller.on_gui_loaded)
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()