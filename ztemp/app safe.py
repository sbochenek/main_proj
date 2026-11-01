# ./app.py
import sys
print("[APP] Początek pliku", flush=True)

#from inference import get_model
print("[APP] Inference OK", flush=True)

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

from .gui.main_window import VideoWindowUI
from video import Video
from models import Models
from controller import AppController
def main():
    app = QApplication(sys.argv)

    # 1. Inicjalizacja warstw
    view = VideoWindowUI()
    models = Models()
    video = Video(models)

    controller = AppController(view, video, models)

    view.show()
    QTimer.singleShot(50, controller.on_gui_loaded)
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()