# controller.py
from gui import VideoWindowUI
import backend

class AppController:
    def __init__(self, view: VideoWindowUI, models: backend.Models,):
        self._view = view
        self._models = models

        # 1. FRONT -> BACKEND:
        # Nasłuchujemy sygnału z GUI i kierujemy go do metody w Backendzie
        # self._view.model_det.addWidget()

        models = self._models.det_models
        self._view.populate_det_models_list(models)

