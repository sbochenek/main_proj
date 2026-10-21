from PyQt5.QtWidgets import (
    QMainWindow, QApplication, QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QScrollArea,
    QPushButton, QLabel, QComboBox, QSlider, QLineEdit, QListWidgetItem, QListWidget
)
from gui_styles.styles import (SCROLL_BAR_STYLE)

from PyQt5.QtCore import Qt
import string

class VideoWindowUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.model_det = self.widget_model_list()
        self.model_pred = self.widget_model_list()
        self.model_track = self.widget_model_list()


        self.video_source_text = QLineEdit()


        self.setWindowTitle("project")
        self.resize(1500, 700)
        self._build_ui()
        self.resize_to_screen_ratio(6/7, 6/7)

        

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

    # lewa strona opcje do modeli
    # prawa strona narzedzia do obrazu i samo video
    def _build_ui(self):
        central = QWidget()
        central.setStyleSheet('background-color: #222327')
        self.setCentralWidget(central)
        
        main_layout = QVBoxLayout(central)
        workspace_layout = QHBoxLayout()
        main_layout.addLayout(workspace_layout)

        # label na samej gorze zeby uklad sprawdzic
        self.tmp_label = QLabel('losowy tekst')



        # Pasek narzędzi dla modeli
        main_models_widget = QWidget()
        main_models_layout = QVBoxLayout()
        main_models_widget.setLayout(main_models_layout)
        main_models_widget.setMaximumWidth(350)

        models_content_widget = QWidget()
        models_content_layout = QVBoxLayout(models_content_widget)
        models_content_layout.setSpacing(20)
        models_content_layout.setContentsMargins(10,20,10,20)
        models_content_layout.setAlignment(Qt.AlignTop)

        models_scroll_area = QScrollArea()
        models_scroll_area.setWidgetResizable(True)
        models_scroll_area.setStyleSheet(SCROLL_BAR_STYLE)
        models_scroll_area.setWidget(models_content_widget)
        main_models_layout.addWidget(models_scroll_area)

        det_widget = self.add_models_widget("modele detekcji obiektow", self.model_det)
        pred_widget = self.add_models_widget("modele predykcji ruchu obiektow", self.model_pred)
        track_widget = self.add_models_widget("modele śledzenia obiektow",self.model_track)
        models_content_layout.addWidget(det_widget)
        models_content_layout.addWidget(pred_widget)
        models_content_layout.addWidget(track_widget)


        # Pasek narzędzi video
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
        self.video_label = QLabel("Podaj źródło video...")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("background:black; color:white;")
        self.video_label.setMinimumSize(800, 500)

        main_video_workspace_layout.addWidget(self.video_label)
        main_video_workspace_layout.addLayout(video_toolbar)

        # main_layout.addWidget(self.tmp_label)
        workspace_layout.addWidget(main_models_widget)
        workspace_layout.addWidget(main_video_workspace_widget)
                

    def resize_main_window(self, width, height):
        self.resize(width, height)
        window_geometry = self.frameGeometry()
        screen_center = QApplication.primaryScreen().availableGeometry().center()
        window_geometry.moveCenter(screen_center)
        self.move(window_geometry.topLeft())

    def add_models_widget(self, text: string, widget_model_list: QListWidgetItem):
        model_widget = QWidget()
        model_widget.setMinimumSize(250,200)
        model_widget.setStyleSheet('background-color: #37393b; border-radius: 10px')

        model_layout = QVBoxLayout()
        model_widget.setLayout(model_layout)

        model_layout.addSpacing(10)
        model_layout.setAlignment(Qt.AlignTop)

        model_text = QLabel(text)
        model_text.setStyleSheet('color: black; font-size: 12pt;')
        model_layout.addWidget(model_text)

        model_layout.addWidget(widget_model_list)

        det_thr = QLabel("Próg detekcji:")
        det_thr.setStyleSheet('color: white')
        model_layout.addWidget(det_thr)

        self.conf_slider = QSlider(Qt.Horizontal)
        self.conf_slider.setRange(10, 90)
        self.conf_slider.setValue(40)
        model_layout.addWidget(self.conf_slider)

        return model_widget

    def widget_model_list(self):
        models_list = QListWidget()
        content_layout = QVBoxLayout(models_list)
        content_layout.setAlignment(Qt.AlignLeft)
        #models_list.setWidgetResizable(True)
        models_list.setStyleSheet(SCROLL_BAR_STYLE)
        return models_list

    def populate_det_models_list(self, file_paths: list[str]):
        for path in file_paths:
            item = QListWidgetItem(path)
            self.model_det.addItem(item)
            print(f'załadowano {item}')

    def populate_pred_models_list(self, file_paths: list[str]):
        for path in file_paths:
            item = QListWidgetItem(path)
            self.model_pred.addItem(item)
            print(f'załadowano {item}')

    def populate_track_models_list(self, file_paths: list[str]):
        for path in file_paths:
            item = QListWidgetItem(path)
            self.model_track.addItem(item)
            print(f'załadowano {item}')


    ## metody dla strony z video
    def get_source_vid(self):
        text = self.video_source_text.text()
        return text

    def next_frame():
        pass

if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv) # sys.argv przekazanie argumentow z systemu (konsoli)

    Qsize = app.primaryScreen().availableSize()
    
    view = VideoWindowUI()
    view.resize_main_window(int(Qsize.width()*6/7), int(Qsize.height()*6/7))
    view.show()

    sys.exit(app.exec_())