# main_app\backend\visualization\frame_process.py
import supervision as sv
from PyQt5.QtCore import QObject, pyqtSignal,  pyqtSlot
import cv2

class FrameProcessor(QObject):
    # Przetworzona klatka
    frame_ready = pyqtSignal(object)

    # Informacja o błędzie
    error_occurred = pyqtSignal(str)

    # Informacja o zakończeniu przetwarzania
    processing_finished = pyqtSignal()

    visualization_options_changed = pyqtSignal(bool, bool, bool)

    def __init__(self, yolo_detection, tracking, predictions):
        super().__init__()
        self.annotator = Annotator()
        self.draw_car_detection = True
        self.draw_park_detection = True
        self.draw_tracking = True
        self.yolo_detection = yolo_detection
        self.tracking = tracking
        self.predictions = predictions

        self.visualization_options_changed.connect(self.set_visualization_options)
    @pyqtSlot(object)
    def process_frame(self, frame):
        car_detection_results = None
        park_detection_results = None
        track_detections = None
        track_labels = None

        try:
            # 1. Detekcja
            if self.yolo_detection.car_det_loaded:
                car_detection_results = self.yolo_detection.detect_cars(frame)
            if self.yolo_detection.park_det_loaded:
                park_detection_results = self.yolo_detection.detect_park_slot(frame)
            # # 2. Tracking
            if self.tracking.loaded_tracker:
                track_detections, track_labels = self.tracking.track_cars(car_detection_results)

            # # 3. Predykcja
            # prediction_results = self.predictions.process(
            #     tracking_results
            # )

            # 4. Wizualizacja
            processed_frame = self.process_visualization(
                frame,
                car_detection_results,
                park_detection_results,
                track_detections,
                track_labels
            )

            # Przekazanie gotowej klatki
            self.frame_ready.emit(processed_frame)
        except Exception as exc:
            self.error_occurred.emit(str(exc))
        finally:
            self.processing_finished.emit()

    def process_visualization(self,frame,car_detection_results,park_detection_results,track_detections,track_labels):

        try:
            if self.draw_park_detection:
                for box in park_detection_results.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cls = int(box.cls[0])
                    label = park_detection_results.names.get(cls, str(cls))
                    conf_val = float(box.conf[0])
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(
                        frame, f"{label} {conf_val:.2f}",
                        (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2
                    )

            if self.draw_tracking:
                frame = self.annotator.box_annotator.annotate(
                    scene=frame.copy(),
                    detections=track_detections
                )

                frame = self.annotator.label_annotator.annotate(
                    scene=frame,
                    detections=track_detections,
                    labels=track_labels
                )

                frame = self.annotator.trace_annotator.annotate(
                    scene=frame,
                    detections=track_detections
                )
                print('rysowanie trackingu')
            
            if self.draw_car_detection:
                for box in car_detection_results.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cls = int(box.cls[0])
                    label = car_detection_results.names.get(cls, str(cls))
                    conf_val = float(box.conf[0])
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(
                        frame, f"{label} {conf_val:.2f}",
                        (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2
                    )
                print('rysowanie tylko detekcji samochodow')
        except Exception as exc:
            self.error_occurred.emit(str(exc))
        finally:
            return frame
            
    
    def set_visualization_options(self, draw_car_detection: bool, draw_park_detection: bool, draw_tracking: bool):
        self.draw_car_detection = draw_car_detection
        self.draw_park_detection = draw_park_detection
        self.draw_tracking = draw_tracking


class Annotator():
  def __init__(self):
    self.box_annotator = sv.BoxAnnotator()
    self.label_annotator = sv.LabelAnnotator()
    self.trace_annotator = sv.TraceAnnotator()