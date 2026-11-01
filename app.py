# ./app.py
import sys
print("[APP] Początek pliku", flush=True)

#from inference import get_model
print("[APP] Inference OK", flush=True)

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

from gui.main_window import VideoWindowUI
from controller import AppController

from backend.visualization.video import Video
from backend.visualization.frame_process import FrameProcessor
from backend.detections.yolo_detection import YOLODetection
from backend.tracking.tracking import Tracking_algorithms
def main():
    app = QApplication(sys.argv)

    # 1. Inicjalizacja warstw
    view = VideoWindowUI()
    yolo_detections = YOLODetection()
    tracking = Tracking_algorithms()
    predictions = 1
    frame_processor = FrameProcessor(yolo_detections, tracking, predictions)
    video = Video()
    
    controller = AppController(view, video, yolo_detections, tracking, frame_processor)

    app.aboutToQuit.connect(controller.shutdown)
    view.show()
    QTimer.singleShot(50, controller.on_gui_loaded)
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()