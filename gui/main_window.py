# ./gui/main_window.py
from PyQt5.QtWidgets import (
    QMainWindow, QApplication, QWidget, QVBoxLayout, QHBoxLayout, QFrame, QScrollArea,
    QPushButton, QLabel, QToolTip, QCheckBox, QLineEdit, QListWidgetItem, QListWidget,
    QSizePolicy,
)

from PyQt5.QtCore import pyqtSignal, QEvent, Qt, QPoint, QSize
from .styles import (SCROLL_BAR_STYLE, SLIDER_STYLE, VIDEO_BUTTON_STYLE,
                     VIDEO_TOOLBAR_STYLE, VIDEO_TIME_LABEL_STYLE, CHECKBOX_STYLE)
from .components import (create_widget_list, create_slider,
                        create_model_widget, create_visualization_options,
                        create_track_widget, create_prediction_widget,
                        CustomRowWidget)

from PyQt5.QtGui import QImage, QPixmap, QCursor
import cv2


class VideoWindowUI(QMainWindow):
    tracker_params_changed = pyqtSignal(str, dict)

    VIDEO_PLACEHOLDER = "Podaj źródło video..."
    SEEK_STEP_S = 5

    TXT_PLAY = "▶  Odtwórz"
    TXT_PAUSE = "❚❚  Pauza"
    TXT_STOP = "■  Stop"

    def __init__(self):
        super().__init__()
        (self.options_container,
         self.checkbox_car_detection,
         self.checkbox_park_detection,
         self.checkbox_tracking,
         self.checkbox_validator,
         self.checkbox_prediction) = create_visualization_options()

        # Opcjonalna detekcja pieszych – zmienia klasy zwracane przez model,
        # a nie tylko rysowanie. Piesi nie biorą udziału w walidacji parkowania.
        self.checkbox_pedestrians = QCheckBox("Wykrywaj pieszych", self.options_container)
        self.checkbox_pedestrians.setStyleSheet(CHECKBOX_STYLE)
        self.checkbox_pedestrians.setChecked(False)
        self.options_container.layout().addWidget(self.checkbox_pedestrians)

        self.model_det_park_spot = create_widget_list()
        self.model_det_cars = create_widget_list()

        # self.rf_model_det_park_spot = create_widget_list()
        # self.rf_model_det_cars = create_widget_list()

        self.track_alg_list = create_widget_list()
        self.pred_alg_list = create_widget_list()

        self.model_det_park_spot.setObjectName("StandardList")
        self.model_det_cars.setObjectName("StandardList")
        # self.rf_model_det_cars.setObjectName("StandardList")
        # self.rf_model_det_park_spot.setObjectName("StandardList")
        self.pred_alg_list.setObjectName("StandardList")

        self.video_source_text = QLineEdit()
        self.video_label = VideoLabel(self.VIDEO_PLACEHOLDER)
        # po Stop ignorujemy klatki, które jeszcze "wiszą" w kolejce
        self._frames_enabled = True

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

        main_models_layout.addWidget(self.options_container)

        models_content_widget = QWidget()
        models_content_layout = QVBoxLayout(models_content_widget)
        models_content_layout.setSpacing(20)
        models_content_layout.setContentsMargins(10,20,10,20)
        models_content_layout.setAlignment(Qt.AlignTop)

        models_scroll_area = QScrollArea()
        models_scroll_area.setWidgetResizable(True)
        models_scroll_area.setStyleSheet(SCROLL_BAR_STYLE)
        models_scroll_area.setWidget(models_content_widget)

        self.slider_det_park_spot, self.park_val_label = create_slider()
        self.slider_det_cars, self.cars_val_label = create_slider()
        widget_det_park_spot = create_model_widget("modele yolo detekcji miejsc parkingowych",
                                                        self.model_det_park_spot,
                                                        self.slider_det_park_spot,
                                                        self.park_val_label
                                                        )
        widget_det_cars = create_model_widget("modele yolo detekcji pojazdów",
                                                  self.model_det_cars,
                                                  self.slider_det_cars,
                                                  self.cars_val_label
                                                  )
        models_content_layout.addWidget(widget_det_cars)
        models_content_layout.addWidget(widget_det_park_spot)

        # self.rf_slider_det_park_spot, self.rf_park_val_label = create_slider()
        # self.rf_slider_det_cars, self.rf_cars_val_label = create_slider()
        # widget_rf_det_park_spot = create_model_widget("modele roboflow detekcji miejsc parkingowych",
        #                                                 self.rf_model_det_park_spot,
        #                                                 self.rf_slider_det_park_spot,
        #                                                 self.rf_park_val_label
        #                                                 )
        # widget_rf_det_cars = create_model_widget("modele roboflow detekcji pojazdów",
        #                                           self.rf_model_det_cars,
        #                                           self.rf_slider_det_cars,
        #                                           self.rf_cars_val_label
        #                                           )
        # models_content_layout.addWidget(widget_rf_det_park_spot)
        # models_content_layout.addWidget(widget_rf_det_cars)

        track_widget = create_track_widget("algorytmy śledzenia obiektow",
                                            self.track_alg_list
                                            )
        models_content_layout.addWidget(track_widget)

        predict_widget = create_prediction_widget("algorytmy predykcji ruchu obiektow",
                                            self.pred_alg_list,
                                            )
        models_content_layout.addWidget(predict_widget)

        main_models_layout.addWidget(models_scroll_area)

        return main_models_widget

    def build_video_panel(self) -> QWidget:
        main_video_workspace_widget = QWidget()
        main_video_workspace_layout = QVBoxLayout()
        main_video_workspace_widget.setLayout(main_video_workspace_layout)

        self.video_source_text.setPlaceholderText('podaj źródło obrazu')
        self.video_source_text.setStyleSheet("background:white; color:black;")
        self.video_source_text.returnPressed.connect(self.get_source_vid)
        main_video_workspace_layout.addWidget(self.video_source_text)

        # Pasek sterowania: [« -5 s] [▶ Odtwórz] [■ Stop] [+5 s »] ...... [00:00 / 00:00]
        toolbar_frame = QFrame()
        toolbar_frame.setObjectName("video_toolbar")
        toolbar_frame.setStyleSheet(VIDEO_TOOLBAR_STYLE)
        video_toolbar = QHBoxLayout(toolbar_frame)
        video_toolbar.setContentsMargins(12, 8, 12, 8)
        video_toolbar.setSpacing(10)

        self.btn_backward = QPushButton(f"«  -{self.SEEK_STEP_S} s")
        self.btn_backward.setToolTip(f"Cofnij o {self.SEEK_STEP_S} s")

        self.btn_play = QPushButton(self.TXT_PLAY)
        self.btn_play.setObjectName("PrimaryVideoButton")
        self.btn_play.setToolTip("Odtwórz / wstrzymaj")

        self.btn_stop = QPushButton(self.TXT_STOP)
        self.btn_stop.setObjectName("StopVideoButton")
        self.btn_stop.setToolTip("Zatrzymaj odtwarzanie")

        self.btn_forward = QPushButton(f"+{self.SEEK_STEP_S} s  »")
        self.btn_forward.setToolTip(f"Przewiń o {self.SEEK_STEP_S} s")

        self.time_label = QLabel("--:-- / --:--")
        self.time_label.setStyleSheet(VIDEO_TIME_LABEL_STYLE)
        self.time_label.setAlignment(Qt.AlignVCenter | Qt.AlignRight)

        video_toolbar.addStretch()
        for btn in (self.btn_backward, self.btn_play, self.btn_stop, self.btn_forward):
            btn.setStyleSheet(VIDEO_BUTTON_STYLE)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFocusPolicy(Qt.NoFocus)
            video_toolbar.addWidget(btn)
        video_toolbar.addStretch()
        video_toolbar.addWidget(self.time_label)

        # Ekran wideo
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("background:black; color:white;")
        self.video_label.setMinimumSize(800, 500)

        # pasek przycisków: wysokość tylko taka, jakiej potrzebują przyciski
        toolbar_frame.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        # wideo: zajmuje całą resztę miejsca; Ignored sprawia, że pixmapa
        # nie "rozpycha" layoutu przy każdej klatce
        self.video_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)

        main_video_workspace_layout.addWidget(self.video_label, 1)
        main_video_workspace_layout.addWidget(toolbar_frame, 0)

        self.set_playback_state(False, False, False)

        return main_video_workspace_widget

    ## stan przycisków odtwarzania
    def set_playback_state(self, running: bool, paused: bool, seekable: bool):
        self.btn_play.setText(self.TXT_PAUSE if running and not paused else self.TXT_PLAY)
        self.btn_stop.setEnabled(running)
        self.btn_forward.setEnabled(running and seekable)
        self.btn_backward.setEnabled(running and seekable)
        if not running:
            self.time_label.setText("--:-- / --:--")
        elif not seekable:
            self.time_label.setText("● NA ŻYWO")

    def update_position(self, position_s: float, duration_s: float):
        self.time_label.setText(f"{_fmt_time(position_s)} / {_fmt_time(duration_s)}")

    def clear_video(self):
        self._frames_enabled = False
        self.video_label.clear()
        self.video_label.setText(self.VIDEO_PLACEHOLDER)

    def enable_frames(self):
        self._frames_enabled = True


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

    # def populate_rf_models_det_park_spot(self, file_paths: list[str]):
    #     for path in file_paths:
    #         item = QListWidgetItem(path)
    #         self.rf_model_det_park_spot.addItem(item)
    #         print(f'załadowano {item}')

    # def populate_rf_models_det_cars(self, file_paths: list[str]):
    #     for path in file_paths:
    #         item = QListWidgetItem(path)
    #         self.rf_model_det_cars.addItem(item)
    #         print(f'załadowano {item}')


    def populate_track_algs(self, algs, get_config):
        for alg in algs:
            item = QListWidgetItem(self.track_alg_list)
            row_widget = CustomRowWidget(
                alg.value,
                self.track_alg_list,
                item,
                params=get_config(alg),
            )
            row_widget.params_changed.connect(self.tracker_params_changed.emit)
            item.setSizeHint(QSize(250, row_widget.height()))
            self.track_alg_list.setItemWidget(item, row_widget)
            print(f"załadowano {item}")

    def populate_pred_algs(self, algs):
        for alg in algs:
            item = QListWidgetItem(alg)
            self.pred_alg_list.addItem(item)
            print(f'załadowano {item.text()}')




    ## metody dla strony z video
    def get_source_vid(self) -> str:
        text = self.video_source_text.text()
        return text

    # ustawienie rozmiarow video przy wlaczeniu aplikacji
    def get_video_size(self):
        return self.video_label.width(), self.video_label.height()

    def display_frame(self, frame):
        if frame is None or not self._frames_enabled:
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

def _fmt_time(seconds: float) -> str:
    seconds = max(0, int(seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


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