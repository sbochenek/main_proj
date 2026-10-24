# ./app.py
import sys

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

from gui import VideoWindowUI
from video import Video
from models import Models
from controller import AppController

def main():
    app = QApplication(sys.argv)

    # 1. Inicjalizacja warstw
    view = VideoWindowUI()
    video = Video()
    models = Models()

    controller = AppController(view, video, models)

    view.show()
    QTimer.singleShot(50, controller.on_gui_loaded)
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()