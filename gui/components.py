# ./gui/components.py

from PyQt5.QtWidgets import (
    QMainWindow, QApplication, QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QScrollArea, QSizePolicy,
    QPushButton, QLabel, QFrame, QSlider, QCheckBox, QListWidgetItem, QListWidget, QMenu, QInputDialog, QWidgetAction, QSpinBox, QDoubleSpinBox, QLineEdit
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
  widget_list = SelectableListWidget()
  widget_list.setSelectionMode(QListWidget.SingleSelection)
  widget_list.setSpacing(4)
  widget_list.setUniformItemSizes(False)

  return widget_list


def create_model_widget(text: str, widget_model_list: QListWidget, slider: QSlider, val_label: str):
  model_widget = QWidget() # glowny kontener danych modeli na widgety
  model_widget.setMinimumSize(250,300)
  model_widget.setStyleSheet('background-color: #37393b; border-radius: 10px')

  model_layout = QVBoxLayout() # sposob ukladania elementow w kontenerze modeli
  model_widget.setLayout(model_layout)
  model_layout.setContentsMargins(10, 8, 10, 8) 
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


def create_track_widget(text: str, widget_model_list: QListWidget, slider: QSlider, val_label: str):
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

class CustomRowWidget(QWidget):
    params_changed = pyqtSignal(str, dict)
    def __init__(self, text, list_widget, item, params=None):
        super().__init__()
        self.text = text
        self.list_widget = list_widget
        self.item = item
        self.params = dict(params) if params is not None else {}

        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background-color: transparent;")
        self.setFixedHeight(32)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8) 
        layout.setSpacing(0)
        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed
        )
        # Etykieta z tekstem
        label = QLabel(text)
        label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        label.setStyleSheet("""
                QLabel {
                    font-size: 10pt;
                    color: #FFFFFF;
                    background-color: transparent;
                }
            """)

        # Przycisk "..."
        btn = QPushButton("...")
        btn.setFixedSize(22, 22)
        btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        btn.setStyleSheet("""
                QPushButton {
                    background-color: #3b3b3b;
                    color: #FFFFFF;
                    font-size: 12px;
                    font-weight: bold;
                    border: 1px solid #5c5c5c;
                    border-radius: 6px;
                }
                QPushButton:hover {
                    background-color: #505050;
                    border: 1px solid #7c7c7c;
                }
                QPushButton:pressed {
                    background-color: #2b2b2b;
                }
            """)

        btn.clicked.connect(lambda: self.show_popup_menu(btn))

        # Dodajemy elementy do layoutu TYLKO RAZ z jawny wyśrodkowaniem w pionie:
        layout.addWidget(label, 1, Qt.AlignVCenter)
        layout.addWidget(btn, 0, Qt.AlignRight | Qt.AlignVCenter)

    def show_popup_menu(self, button):
        """Tworzy menu z listą parametrów i polami do edycji."""
        menu = QMenu(self)
        
        if not self.params:
            menu.addAction("Brak parametrów do edycji").setEnabled(False)
        else:
            for key, value in self.params.items():
                # Tworzymy akcję, która będzie zawierać własny widget
                action = QWidgetAction(menu)
                
                # Kontener na etykietę i pole edycyjne
                row_widget = QWidget()
                row_layout = QHBoxLayout(row_widget)
                row_layout.setContentsMargins(10, 4, 10, 4)
                row_layout.setSpacing(10)
                
                # Etykieta z nazwą parametru
                label = QLabel(key)
                label.setMinimumWidth(120) # żeby ładnie wyrównać pola
                label.setStyleSheet("color: white;")
                row_layout.addWidget(label)
                
                # Pole edycyjne w zależności od typu
                if isinstance(value, bool):
                    editor = QCheckBox()
                    editor.setChecked(value)
                    # Checkbox nie ma sygnału textChanged, podpinamy się pod stan
                    editor.stateChanged.connect(
                        lambda state, k=key, w=editor: self._on_param_edited(k, w.isChecked())
                    )
                elif isinstance(value, int):
                    editor = QSpinBox()
                    editor.setRange(-10000, 10000)
                    editor.setValue(value)
                    editor.setKeyboardTracking(False)
                    editor.valueChanged.connect(
                        lambda val, k=key: self._on_param_edited(k, val)
                    )
                elif isinstance(value, float):
                    editor = QDoubleSpinBox()
                    editor.setRange(-10000.0, 10000.0)
                    editor.setDecimals(4)
                    editor.setValue(value)
                    editor.setSingleStep(0.05)
                    editor.setKeyboardTracking(False)
                    editor.valueChanged.connect(
                        lambda val, k=key: self._on_param_edited(k, val)
                    )
                elif key == "cmc_method":
                    editor = QComboBox()
                    editor.addItems(["sparseOptFlow", "sift", "ecc"])
                    editor.setCurrentText(value)
                    editor.currentTextChanged.connect(lambda t, k=key: self._on_param_edited(k, t))
                else:
                    editor = QLineEdit(str(value))
                    editor.editingFinished.connect(
                        lambda k=key, w=editor: self._on_param_edited(k, w.text())
                    )

                # Stylizacja pól edycyjnych, żeby pasowały do ciemnego motywu
                editor.setStyleSheet("""
                    QSpinBox, QDoubleSpinBox, QLineEdit {
                        background-color: #2b2b2b;
                        color: white;
                        border: 1px solid #555;
                        border-radius: 4px;
                        padding: 2px;
                    }
                    QCheckBox::indicator {
                        width: 16px; height: 16px;
                        border-radius: 3px;
                        border: 2px solid #777;
                        background: #2b2b2b;
                    }
                    QCheckBox::indicator:checked {
                        background-color: #007acc;
                        border: 2px solid #007acc;
                    }
                """)
                
                row_layout.addWidget(editor)
                
                # Ustawiamy nasz rząd jako zawartość akcji
                action.setDefaultWidget(row_widget)
                menu.addAction(action)

        # Wyświetlamy menu pod przyciskiem
        menu.exec_(button.mapToGlobal(QPoint(0, button.height())))

    def _on_param_edited(self, key, new_value):
        self.params[key] = new_value
        self.params_changed.emit(self.text, {key: new_value})


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