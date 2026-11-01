# main_app/controller.py
from backend.detections.yolo_detection import ModelType
from PyQt5.QtCore import QThread, Qt

class AppController:
    def __init__(self, view, video, yolo_detection, tracking, frame_processor):
        self._view = view
        self._video = video

        self._yolo_models = yolo_detection
        self._tracking = tracking

        self._frame_processor = frame_processor

        self._processing_thread = QThread()

        self._video.frame_ready.connect(self._view.display_frame)
        self._video.error_occurred.connect(
            lambda message: print(f"Błąd wideo: {message}")
        )
        # ladowanie modeli do gui
        self._view.populate_models_det_park_spot(self._yolo_models.det_park_list)
        self._view.populate_models_det_cars(self._yolo_models.det_cars_list)

        self._view.populate_track_algs(self._tracking.trackers)
        # self._view.populate_pred_algs(self._trackingpredictors)
        
        # polaczenie eventu zmiany screenu z zmiana video w backendzie
        self._view.video_label.size_changed.connect(self.handle_video_screen_reseize)
        # polaczene eventu zmiany zrodla video przez klawisz enter
        self._view.video_source_text.returnPressed.connect(self.handle_video_source_change)

        # laczenei funkcji wybierajacych modele z models
        self._view.model_det_park_spot.itemClicked.connect(
            lambda item: self.handle_model_change(ModelType.DET_PARK_SPOT, item)
        )
        self._view.model_det_cars.itemClicked.connect(
            lambda item: self.handle_model_change(ModelType.DET_CAR, item)
        )
        # self._view.track_alg_list.itemClicked.connect(
        #     lambda item: self.handle_tracker_change(item)
        # )

        self._view.slider_det_park_spot.sliderReleased.connect(lambda: self.handle_slider_release_park_det(self._view.slider_det_park_spot.value()))
        self._view.slider_det_cars.sliderReleased.connect(lambda: self.handle_slider_release_cars_det(self._view.slider_det_cars.value()))

    def on_error(self, message):
        print(f"Błąd: {message}")

    def start_video(self, source):

        if self._video.isRunning():
            self.stop_video()

        if self._video.change_video_source(source):
            self._video.start()

    def stop_video(self):

        self._video.stop()

    def shutdown(self):

        # Zatrzymanie odczytu klatek
        self._video.stop()

        # Zakończenie wątku przetwarzania
        self._processing_thread.quit()
        self._processing_thread.wait()

    def __del__(self):

        if hasattr(self, "_processing_thread"):
            if self._processing_thread.isRunning():
                self._processing_thread.quit()
                self._processing_thread.wait()


    def on_gui_loaded(self):
        initial_vid_size = self._view.get_video_size()
        self._video.resize_video_to_dimensions(initial_vid_size[0],initial_vid_size[1])
    
    def handle_video_source_change(self):
        source_text = self._view.get_source_vid()

        if not source_text.strip():
            print("Ścieżka wideo jest pusta!")
            return

        if self._video.change_video_source(source_text):
            self._video.start()
    

    def handle_video_screen_reseize(self, width, heigh):
        self._video.resize_video_to_dimensions(width, heigh)


    ## funkcje dla modeli
    def handle_model_change(self, model_type, item):
        print(f"handle_model_change typ: {model_type}, item: {item.text()}")
        model_name = item.text()
        self._yolo_models.set_active_model(model_type, model_name)

    def handle_slider_release_park_det(self, value):
        self._yolo_models.change_park_thr(value/100)

    def handle_slider_release_cars_det(self, value):
        self._yolo_models.change_cars_thr(value/100)
