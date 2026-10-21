import sys

from PyQt5.QtWidgets import QApplication

from gui import VideoWindowUI
import backend
from controller import AppController

def main():
    app = QApplication(sys.argv)

    # 1. Inicjalizacja warstw
    view = VideoWindowUI()
    models = backend.Models()

    controller = AppController(view, models)

    view.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()