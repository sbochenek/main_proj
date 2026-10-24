# ./controller.py
from gui import VideoWindowUI
from backend import BackendManager

class AppController:
    def __init__(self, view, backend_manager):
        self._view = view
        self._models = backend_manager.models
        self._video = backend_manager.video

        models = self._models.det_models
        self._view.populate_det_models_list(models)

        # polaczenie eventu zmiany screenu z zmiana video w backendzie
        self._view.video_label.size_changed.connect(self.handle_video_screen_reseize)
        # polaczene eventu zmiany zrodla video przez klawisz enter
        self._view.video_source_text.returnPressed.connect(self.handle_video_source_change)

        # Podłączenie sygnału z backendu (Publisher) do metody w widoku (Subscriber)
        self._video.frame_ready.connect(self._view.display_frame)


    def on_gui_loaded(self):
        initial_vid_size = self._view.get_video_size()
        self._video.resize_video_to_dimensions(initial_vid_size[0],initial_vid_size[1])
    
    def handle_video_source_change(self):
        source_text = self._view.get_source_vid()
        if not source_text.strip():
            print("Ścieżka wideo jest pusta!")
            return

        print(f"Kontroler przesłał do backendu: {source_text}")

        self._video.change_video_source(source_text)
        self.handle_start_video()
    

    def handle_video_screen_reseize(self, width, heigh):
        self._video.resize_video_to_dimensions(width, heigh)



    def handle_start_video(self):
        self._video.start()