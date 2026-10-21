# controller.py
from gui import VideoWindowUI
from backend import BackendManager

class AppController:
    def __init__(self, view, backend_manager):
        self._view = view
        self._models = backend_manager.models
        self._video = backend_manager.video

        self._view.video_source_text.returnPressed.connect(self.handle_video_source)
        # 1. FRONT -> BACKEND:
        # Nasłuchujemy sygnału z GUI i kierujemy go do metody w Backendzie
        # self._view.model_det.addWidget()

        models = self._models.det_models
        self._view.populate_det_models_list(models)

    def handle_video_source(self):
        source_text = self._view.get_source_vid()
        if not source_text.strip():
            print("Ścieżka wideo jest pusta!")
            return

        print(f"Kontroler przesłał do backendu: {source_text}")

        self._video.set_video_source(source_text)