# ./controller.py
from gui import VideoWindowUI
from video import Video
from models import ModelType

class AppController:
    def __init__(self, view, video, models):
        self._view = view
        self._models = models
        self._video = video

        det_models = self._models.det_models

        # ladowanie modeli do gui
        self._view.populate_det_models_list(det_models)
        self._view.populate_models_det_park_spot(self._models.models_det_park_spot)
        
        # polaczenie eventu zmiany screenu z zmiana video w backendzie
        self._view.video_label.size_changed.connect(self.handle_video_screen_reseize)
        # polaczene eventu zmiany zrodla video przez klawisz enter
        self._view.video_source_text.returnPressed.connect(self.handle_video_source_change)

        # laczenei funkcji wybierajacych modele z models
        self._view.model_det_park_spot.itemClicked.connect(
            lambda item: self.handle_model_change(ModelType.DET_PARK_SPOT, item)
        )

        # Podłączenie sygnału z backendu (Publisher) do metody w widoku (Subscriber)
        self._video.frame_ready.connect(self.handle_frame_processing)

    def handle_frame_processing(self, frame):
        processed_frame = self._models.process_frame(frame)
        self._view.display_frame(processed_frame)


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


    ## funkcje dla modeli
    def handle_model_change(self, model_type, item):
        model_name = item.text()
        self._models.set_active_model(model_type, model_name)