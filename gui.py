# ./gui.py
from PyQt5.QtWidgets import (
    QMainWindow, QApplication, QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QScrollArea,
    QPushButton, QLabel, QToolTip, QSlider, QLineEdit, QListWidgetItem, QListWidget,
)

from PyQt5.QtCore import pyqtSignal, QEvent, Qt, QPoint
from gui_styles.styles import (SCROLL_BAR_STYLE, SLIDER_STYLE)


from PyQt5.QtGui import QImage, QPixmap, QCursor
import cv2


class VideoWindowUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.model_det_park_spot = self.widget_model_list()
        self.model_det_cars = self.widget_model_list()


        self.video_source_text = QLineEdit()
        self.video_label = VideoLabel("Podaj źródło video...")

        self.setWindowTitle("project")
        self.resize(1500, 700)
        self._build_ui()
        self.resize_to_screen_ratio(6/7, 6/7)

    # lewa strona opcje do modeli
    # prawa strona narzedzia do obrazu i samo video
    def _build_ui(self):
        central = QWidget()
        central.setStyleSheet('background-color: #222327')
        self.setCentralWidget(central)
        
        main_layout = QVBoxLayout(central)
        workspace_layout = QHBoxLayout()
        main_layout.addLayout(workspace_layout)

        models_panel = self.build_models_panel()
        video_panel = self.build_video_panel()

        workspace_layout.addWidget(models_panel)
        workspace_layout.addWidget(video_panel)

    def build_models_panel(self) -> QWidget:
        main_models_widget = QWidget()
        main_models_widget.setMaximumWidth(350)
        main_models_layout = QVBoxLayout(main_models_widget)
    
        models_content_widget = QWidget()
        models_content_layout = QVBoxLayout(models_content_widget)
        models_content_layout.setSpacing(20)
        models_content_layout.setContentsMargins(10,20,10,20)
        models_content_layout.setAlignment(Qt.AlignTop)

        models_scroll_area = QScrollArea()
        models_scroll_area.setWidgetResizable(True)
        models_scroll_area.setStyleSheet(SCROLL_BAR_STYLE)
        models_scroll_area.setWidget(models_content_widget)

        widget_det_park_spot, self.slider_det_park_spot = self._create_model_card("modele detekcji miejsc parkingowych", self.model_det_park_spot)
        widget_det_cars, self.slider_det_cars = self._create_model_card("modele detekcji pojazdów", self.model_det_cars)
        models_content_layout.addWidget(widget_det_park_spot)
        models_content_layout.addWidget(widget_det_cars)

        track_widget, self.track_alg_list = self._create_track_alg_card("algorytmy śledzenia obiektow")
        models_content_layout.addWidget(track_widget)


        main_models_layout.addWidget(models_scroll_area)

        return main_models_widget

    def build_video_panel(self) -> QWidget:
        main_video_workspace_widget = QWidget()
        main_video_workspace_layout = QVBoxLayout()
        main_video_workspace_widget.setLayout(main_video_workspace_layout)
        video_toolbar = QHBoxLayout()

        self.video_source_text.setPlaceholderText('podaj źródło obrazu')
        self.video_source_text.setStyleSheet("background:white; color:black;")
        self.video_source_text.returnPressed.connect(self.get_source_vid)
        main_video_workspace_layout.addWidget(self.video_source_text)

        self.btn_open = QPushButton("Play")
        video_toolbar.addWidget(self.btn_open)

        self.btn_play = QPushButton("Stop")
        video_toolbar.addWidget(self.btn_play)

        self.btn_forward = QPushButton("Forward")
        video_toolbar.addWidget(self.btn_forward)

        self.btn_backward = QPushButton("Backward")
        video_toolbar.addWidget(self.btn_backward)

        # Ekran wideo
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("background:black; color:white;")
        self.video_label.setMinimumSize(800, 500)

        main_video_workspace_layout.addWidget(self.video_label)
        main_video_workspace_layout.addLayout(video_toolbar)
        
        return main_video_workspace_widget

    def _create_model_card(self, text: str, widget_model_list: QListWidget):
        """funkcja przygotowujaca widget w ktorym beda umieszczone modele"""
        model_widget = QWidget()
        model_widget.setMinimumSize(250,200)
        model_widget.setStyleSheet('background-color: #37393b; border-radius: 10px')

        model_layout = QVBoxLayout()
        model_widget.setLayout(model_layout)

        model_layout.addSpacing(10)
        model_layout.setAlignment(Qt.AlignTop)

        model_text = QLabel(text)
        model_text.setStyleSheet('color: white; font-size: 12pt;')
        model_layout.addWidget(model_text)

        model_layout.addWidget(widget_model_list)

        layout_thr = QHBoxLayout()
        det_thr = QLabel("Próg detekcji:")
        det_thr.setStyleSheet('color: white')
        val_label = QLabel("40")  # Startowa wartość
        val_label.setStyleSheet('color: white; font-weight: bold; font-size: 16')

        layout_thr.addWidget(det_thr)
        layout_thr.addStretch()
        layout_thr.addWidget(val_label)
        model_layout.addLayout(layout_thr)

        conf_slider = QSlider(Qt.Horizontal)
        conf_slider.setRange(0, 100)
        conf_slider.setValue(40)
        conf_slider.setStyleSheet(SLIDER_STYLE)        
        model_layout.addWidget(conf_slider)

        conf_slider.valueChanged.connect(lambda val: val_label.setText(str(val))) # zmiana napisu w gui
        return model_widget, conf_slider

    def widget_model_list(self) -> QListWidget:
        models_list = QListWidget()
        content_layout = QVBoxLayout(models_list)
        content_layout.setAlignment(Qt.AlignLeft)
        #models_list.setWidgetResizable(True)
        models_list.setStyleSheet(SCROLL_BAR_STYLE)

        return models_list
    
    def _create_track_alg_card(self, text):
        track_widget = QWidget()
        track_widget.setMinimumSize(250,200)
        track_widget.setStyleSheet('background-color: #37393b; border-radius: 10px')

        track_layout = QVBoxLayout()
        track_widget.setLayout(track_layout)

        track_layout.addSpacing(10)
        track_layout.setAlignment(Qt.AlignTop)

        model_text = QLabel(text)
        model_text.setStyleSheet('color: black; font-size: 12pt;')
        track_layout.addWidget(model_text)

        track_alg_list = QListWidget()
        content_layout = QVBoxLayout(track_alg_list)
        content_layout.setAlignment(Qt.AlignLeft)
        #models_list.setWidgetResizable(True)
        track_alg_list.setStyleSheet(SCROLL_BAR_STYLE)
        track_layout.addWidget(track_alg_list)

        layout_thr = QHBoxLayout()
        # det_thr = QLabel("Próg detekcji:")
        # det_thr.setStyleSheet('color: white')
        # val_label = QLabel("40")  # Startowa wartość
        # val_label.setStyleSheet('color: white; font-weight: bold; font-size: 16')

        # layout_thr.addWidget(det_thr)
        layout_thr.addStretch()
        # layout_thr.addWidget(val_label)
        track_layout.addLayout(layout_thr)

        # conf_slider = QSlider(Qt.Horizontal)
        # conf_slider.setRange(0, 100)
        # conf_slider.setValue(40)
        # conf_slider.setStyleSheet(SLIDER_STYLE)        
        # track_layout.addWidget(conf_slider)

        # conf_slider.valueChanged.connect(lambda val: val_label.setText(str(val))) # zmiana napisu w gui
        return track_widget, track_alg_list




    def populate_models_det_park_spot(self, file_paths: list[str]):
        for path in file_paths:
            item = QListWidgetItem(path)
            self.model_det_park_spot.addItem(item)
            print(f'załadowano {item}')

    def populate_models_det_cars(self, file_paths: list[str]):
        for path in file_paths:
            item = QListWidgetItem(path)
            self.model_det_cars.addItem(item)
            print(f'załadowano {item}')

    def populate_track_algs(self, algs):
        for alg in algs:
            item = QListWidgetItem(alg.value)
            self.track_alg_list.addItem(item)
            print(f'załadowano {item}')





    ## metody dla strony z video
    def get_source_vid(self) -> str:
        text = self.video_source_text.text()
        return text

    # ustawienie rozmiarow video przy wlaczeniu aplikacji
    def get_video_size(self):
        return self.video_label.width(), self.video_label.height()

    def display_frame(self, frame):
        if frame is None:
            return

        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        q_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_image)
        
        self.video_label.setPixmap(pixmap.scaled(
            self.video_label.width(), 
            self.video_label.height(), 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        ))



    ## metody do zmiany rozmiarow aplikacji
    def resize_main_window(self, width, height):
        self.resize(width, height)
        window_geometry = self.frameGeometry()
        screen_center = QApplication.primaryScreen().availableGeometry().center()
        window_geometry.moveCenter(screen_center)
        self.move(window_geometry.topLeft())

    # zmiana rozmiarow calej aplikacje zeby zajmowala wiekszosc ekranu
    def resize_to_screen_ratio(self, width_ratio: float = 6/7, height_ratio: float = 6/7):
        screen = QApplication.primaryScreen()
        
        if screen:
            screen_size = screen.geometry()
            target_width = int(screen_size.width() * width_ratio)
            target_height = int(screen_size.height() * height_ratio)
            
            # Ustawiamy rozmiar okna
            self.resize(target_width, target_height)

            self.center_on_screen(screen_size, target_width, target_height)

    def center_on_screen(self, screen_size, width, height):
        x = (screen_size.width() - width) // 2
        y = (screen_size.height() - height) // 2
        self.move(x, y)


    def show_value_tooltip(self, value):
        # Pobieramy aktualną pozycję kursora myszy na ekranie
        cursor_pos = QCursor.pos()
        
        # Poprawne wywołanie dymku systemowego PyQt
        QToolTip.showText(cursor_pos, f"Próg: {value}", self)

class VideoLabel(QLabel):
    size_changed = pyqtSignal(int, int)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        width = self.width()
        height = self.height()
        
        self.size_changed.emit(width, height)
        print(f"video label size w: {width}, h: {height}")


if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv) # sys.argv przekazanie argumentow z systemu (konsoli)

    Qsize = app.primaryScreen().availableSize()
    
    view = VideoWindowUI()
    view.resize_main_window(int(Qsize.width()*6/7), int(Qsize.height()*6/7))
    view.show()

    sys.exit(app.exec_())