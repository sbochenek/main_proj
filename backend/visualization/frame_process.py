# main_app\backend\visualization\frame_process.py
import supervision as sv
from PyQt5.QtCore import QObject, pyqtSignal,  pyqtSlot
import cv2
import numpy as np

class FrameProcessor(QObject):
    # Przetworzona klatka
    frame_ready = pyqtSignal(object)

    # Informacja o błędzie
    error_occurred = pyqtSignal(str)

    # Informacja o zakończeniu przetwarzania
    processing_finished = pyqtSignal()

    visualization_options_changed = pyqtSignal(bool, bool, bool, bool)

    def __init__(self, yolo_detection, tracking, predictions, park_validator):
        super().__init__()
        self.annotator = Annotator()# todo: dodac annotatora dla kazdej opcji
        self.draw_car_detection = False
        self.draw_park_detection = False
        self.draw_tracking = False
        self.draw_validation = False
        self.yolo_detection = yolo_detection
        self.tracking = tracking
        self.predictions = predictions
        self.park_validator = park_validator

        self.visualization_options_changed.connect(self.set_visualization_options)
    @pyqtSlot(object)
    def process_frame(self, frame):
        car_detection_results = None
        park_detection_results = None
        track_detections = None
        track_labels = None
        validation_labels = None
        car_dets_val = None
        try:
            # 1. Detekcja
            if self.yolo_detection.car_det_loaded:
                car_detection_results = self.yolo_detection.detect_cars(frame)
            if self.yolo_detection.park_det_loaded:
                park_detection_results = self.yolo_detection.detect_park_slot(frame)
            # # 2. Tracking
            if self.tracking.loaded_tracker:
                track_detections, track_labels = self.tracking.track_cars(car_detection_results)
            if self.draw_validation:
                car_dets_val, validation_labels = self.park_validator.validate(car_detection_results, park_detection_results, self.tracking.is_tracking_enabled)
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
                track_labels,
                validation_labels,
                car_dets_val
            )

            # Przekazanie gotowej klatki
            self.frame_ready.emit(processed_frame)
        except Exception as exc:
            self.error_occurred.emit(str(exc))
        finally:
            self.processing_finished.emit()


    def process_visualization(self,frame,
                              car_detection_results,
                              park_detection_results,
                              track_detections,
                              track_labels,
                              validation_labels,
                              car_dets_val):

        try:
            if self.draw_park_detection:
                print("rysowanie wykryc parkingow")
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
                print("rysowanie trackingu")
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
                print('rysowanie tylko detekcji samochodow')
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

            if self.draw_validation:
                print("start rysowania walidacji")
                frame = self.draw_validation_frame(frame, car_dets_val, validation_labels)

        except Exception as exc:
            self.error_occurred.emit(str(exc))
        finally:
            return frame
            
    def draw_validation_frame(self, frame, detections, labels):
        annotated_frame = frame
        custom_palette = sv.ColorPalette.from_hex([
            "#00FF00",  # zielony
            "#FF0000",  # czerwony
            "#FFFF00"   # żółty
        ])
        self.annotator.box_annotator.color = custom_palette
        self.annotator.box_annotator.color_lookup = sv.ColorLookup.CLASS
        self.annotator.label_annotator.color = custom_palette
        self.annotator.label_annotator.color_lookup = sv.ColorLookup.CLASS

        new_class_ids = []
        for label in labels:
            if "Poprawne parkowanie" in label:
                new_class_ids.append(0)
            elif "Niepoprawne parkowanie" in label:
                new_class_ids.append(1) 
            else:
                new_class_ids.append(2)
        detections.class_id = np.array(new_class_ids, dtype=int)
        annotated_frame = frame.copy()

        annotated_frame = self.annotator.box_annotator.annotate(
            scene=annotated_frame,
            detections=detections
        )
        annotated_frame = self.annotator.label_annotator.annotate(
            scene=annotated_frame, 
            detections=detections, 
            labels=labels
        )
        return annotated_frame

    
    def set_visualization_options(self, draw_car_detection: bool, draw_park_detection: bool, draw_tracking: bool, draw_validation: bool):
        self.draw_car_detection = draw_car_detection
        self.draw_park_detection = draw_park_detection
        self.draw_tracking = draw_tracking
        self.draw_validation = draw_validation


class Annotator():
    def __init__(self):
        self.box_annotator = sv.BoxAnnotator()
        self.label_annotator = sv.LabelAnnotator()
        self.trace_annotator = sv.TraceAnnotator()

    def reset_traces(self):
        if hasattr(self.trace_annotator, 'reset'):
            self.trace_annotator.reset()