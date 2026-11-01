# ./gui/components.py

from PyQt5.QtWidgets import (
    QMainWindow, QApplication, QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QScrollArea,
    QPushButton, QLabel, QFrame, QSlider, QCheckBox, QListWidgetItem, QListWidget,
    )
from PyQt5.QtCore import pyqtSignal, QEvent, Qt, QPoint

from .styles import (QLIST_WIDGET_STYLE, SLIDER_STYLE, CHECKBOX_STYLE, OPTIONS_CONTAINER_STYLE)

def create_slider():
  val_label = QLabel("40%")  # Startowa wartość
  val_label.setStyleSheet('color: white; font-weight: bold; font-size: 16')
  conf_slider = QSlider(Qt.Horizontal)
  conf_slider.setRange(0, 100)
  conf_slider.setValue(40)
  conf_slider.setStyleSheet(SLIDER_STYLE)
  conf_slider.valueChanged.connect(lambda val: val_label.setText(f"{str(val)}%")) # zmiana napisu w gui
  return conf_slider, val_label


def create_widget_list() -> QListWidget:
  models_list = SelectableListWidget()
  models_list.setSelectionMode(QListWidget.SingleSelection)
  content_layout = QVBoxLayout(models_list)
  content_layout.setAlignment(Qt.AlignLeft)
  #models_list.setWidgetResizable(True)

  return models_list


def create_model_widget(text: str, widget_model_list: QListWidget, slider: QSlider, val_label: str):
  model_widget = QWidget() # glowny kontener danych modeli na widgety
  model_widget.setMinimumSize(250,300)
  model_widget.setStyleSheet('background-color: #37393b; border-radius: 10px')

  model_layout = QVBoxLayout() # sposob ukladania elementow w kontenerze modeli
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
  layout_thr.addWidget(det_thr)
  layout_thr.addStretch()
  layout_thr.addWidget(val_label)
  model_layout.addLayout(layout_thr)
    
  model_layout.addWidget(slider)

  return model_widget

def create_visualization_options():
    options_container = QFrame()
    options_container.setObjectName("options_container")
    options_container.setStyleSheet(OPTIONS_CONTAINER_STYLE)

    options_layout = QVBoxLayout(options_container)
    options_layout.setContentsMargins(12, 10, 12, 10)
    options_layout.setSpacing(8)

    checkbox_car_detection = QCheckBox("Detekcja pojazdów", options_container)
    checkbox_park_detection = QCheckBox("Detekcja miejsc parkingowych", options_container)
    checkbox_tracking = QCheckBox("Tracking", options_container)
    checkbox_validator = QCheckBox("walidacja parkowania", options_container)
    
    checkbox_validator.setChecked(False)
    checkbox_car_detection.setChecked(False)
    checkbox_park_detection.setChecked(False)
    checkbox_tracking.setChecked(False)

    for checkbox in (
        checkbox_car_detection,
        checkbox_park_detection,
        checkbox_tracking,
        checkbox_validator
    ):
        checkbox.setStyleSheet(CHECKBOX_STYLE)
        options_layout.addWidget(checkbox)

    return (
        options_container,
        checkbox_car_detection,
        checkbox_park_detection,
        checkbox_tracking,
        checkbox_validator
    )

class SelectableListWidget(QListWidget):
    def __init__(self):
        super().__init__()

        self.setSelectionMode(QListWidget.SingleSelection)
        self.setSelectionBehavior(QListWidget.SelectItems)
        self.setFocusPolicy(Qt.NoFocus)
        self.setStyleSheet(QLIST_WIDGET_STYLE)

        self.itemClicked.connect(self.on_item_clicked)

        self.active_item = None

    def on_item_clicked(self, item: QListWidgetItem):
        if self.active_item is item:
            self.clearSelection()
            self.active_item = None
        else:
            self.active_item = item
            item.setSelected(True)