import sys

from PyQt5.QtWidgets import QApplication

from gui import VideoWindowUI
from backend import BackendManager
from controller import AppController

def main():
    app = QApplication(sys.argv)

    # 1. Inicjalizacja warstw
    view = VideoWindowUI()
    backend = BackendManager()

    controller = AppController(view, backend)

    view.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()