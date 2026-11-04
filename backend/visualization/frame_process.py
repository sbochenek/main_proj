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

    def __init__(self, yolo_detection, rf_detections, tracking, predictions, park_validator):
        super().__init__()
        self.yolo_det_annotator = CarDetectionAnnotator()
        self.rf_det_annotator = CarDetectionAnnotator()
        self.park_annotator = ParkDetectionAnnotator()
        self.tracker_annotator = TrackingAnnotator()
        # self.predictions_annotator = Annotator()
        self.validation_annotator = ValidationAnnotator()

        self.draw_car_detection = False
        self.draw_park_detection = False
        self.draw_tracking = False
        self.draw_validation = False
        self.rf_detections = rf_detections
        self.yolo_detection = yolo_detection
        self.tracking = tracking
        self.predictions = predictions
        self.park_validator = park_validator

        self.visualization_options_changed.connect(self.set_visualization_options)

    @pyqtSlot(object)
    def process_frame(self, frame):
        car_detection_results = None
        car_detection_labels = None
        car_names = None

        park_detection_results = None
        park_detection_labels = None
        park_names = None

        track_detections = None
        track_labels = None

        validation_labels = None
        parked_cars_det_validation = None
        try:
            # Detekcja pojazdow yolo
            if self.yolo_detection.car_det_loaded:
                results = self.yolo_detection.detect_cars(frame)
                if results is not None:
                    car_names = results.names
                    car_detection_results = sv.Detections.from_ultralytics(results)
                    car_detection_labels = [
                        f"{car_names[cls_id]} {conf:.2f}"
                        for cls_id, conf in zip(car_detection_results.class_id,
                                                car_detection_results.confidence)
                    ]
            # Detekcja pojazdow roboflow
            elif self.rf_detections.car_det_loaded:
                result = self.rf_detections.detect_cars(frame)
                if result is not None:
                    car_detection_results = sv.Detections(
                        xyxy=result.xyxy,
                        confidence=result.confidence,
                        class_id=result.class_id
                    )

            # detekcja miejsc parkingowych YOLO
            if self.yolo_detection.park_det_loaded:
                results = self.yolo_detection.detect_park_slot(frame)
                if results is not None:
                    park_names = results.names
                    park_detection_results = sv.Detections.from_ultralytics(results)
                    park_detection_labels = [
                        f"{park_names[cls_id]} {conf:.2f}"
                        for cls_id, conf in zip(park_detection_results.class_id,
                                                park_detection_results.confidence)
                    ]
            # detekcja miejsc parkingowych ROBOFLOW
            elif self.rf_detections.park_det_loaded:
                result = self.rf_detections.detect_park_slot(frame)
                park_detection_results = sv.Detections(
                        xyxy=result.xyxy,
                        confidence=result.confidence,
                        class_id=result.class_id
                        )
                park_names = self.rf_detections.park_class_names
                park_detection_labels = [
                    f"{park_names[cls_id]} {conf:.2f}"
                    for cls_id, conf in zip(
                        park_detection_results.class_id,
                        park_detection_results.confidence
                    )
                ]

            # Tracking pojazdów
            if self.tracking.loaded_tracker:
                track_detections, track_labels = self.tracking.track_cars(car_detection_results, car_names, frame)

            # walidacja parkowania
            if self.draw_validation:
                parked_cars_det_validation, validation_labels = self.park_validator.validate(car_detection_results, park_detection_results, self.tracking.is_tracking_enabled)
            
            #  Predykcja
            # prediction_results = self.predictions.process(
            #     tracking_results
            # )

            # 4. Wizualizacja
            processed_frame = self.process_visualization( frame,
                car_detection_results, car_detection_labels,
                park_detection_results, park_detection_labels,
                track_detections, track_labels,
                validation_labels, parked_cars_det_validation
            )

            # Przekazanie gotowej klatki
            self.frame_ready.emit(processed_frame)
        except Exception as exc:
            self.error_occurred.emit(str(exc))
        finally:
            self.processing_finished.emit()


    def process_visualization(self, frame,
        car_detection_results, car_detection_labels,
        park_detection_results, park_detection_labels,
        track_detections, track_labels,
        validation_labels, car_dets_val):

        try:
            if self.draw_park_detection:
                frame = self.park_annotator.annotate(frame, park_detection_results, park_detection_labels)

            if self.draw_tracking:
                frame = self.tracker_annotator.annotate(frame, track_detections, track_labels)
                
            if self.draw_car_detection:
                frame = self.yolo_det_annotator.annotate(frame, car_detection_results, car_detection_labels)

            if self.draw_validation:
                frame = self.validation_annotator.annotate(frame, car_dets_val, validation_labels)

        except Exception as exc:
            self.error_occurred.emit(str(exc))
        finally:
            return frame

    def set_visualization_options(self, draw_car_detection: bool, draw_park_detection: bool, draw_tracking: bool, draw_validation: bool):
        self.draw_car_detection = draw_car_detection
        self.draw_park_detection = draw_park_detection
        self.draw_tracking = draw_tracking
        self.draw_validation = draw_validation




class BaseAnnotator:
    """Bazowy annotator – jedna odpowiedzialność: rysowanie jednego typu detekcji."""
    def annotate(self, frame, detections, labels=None) -> np.ndarray:
        raise NotImplementedError


class CarDetectionAnnotator(BaseAnnotator):
    """Rysuje detekcje samochodów (YOLO lub Roboflow) zielone boxy + label."""
    def __init__(self):
        color = sv.Color(r=0, g=255, b=0)
        self.box_annotator = sv.BoxAnnotator(color=color, thickness=2)
        self.label_annotator = sv.LabelAnnotator(
            text_color=color, text_scale=0.6, text_thickness=2
        )

    def annotate(self, frame, detections, labels=None):
        if detections is None or len(detections) == 0:
            return frame
        frame = self.box_annotator.annotate(scene=frame, detections=detections)
        if labels is not None and len(labels) == len(detections):
            frame = self.label_annotator.annotate(
                scene=frame, detections=detections, labels=labels
            )
        return frame


class ParkDetectionAnnotator(BaseAnnotator):
    """Rysuje detekcje miejsc parkingowych zielone boxy + label."""
    def __init__(self):
        self.color = sv.Color(r=0, g=255, b=0)
        self.box_annotator = sv.BoxAnnotator(color=self.color, thickness=2)
        self.label_annotator = sv.LabelAnnotator(
            text_color=self.color, text_scale=0.6, text_thickness=2
        )

    def annotate(self, frame, detections, labels=None):
        if detections is None or len(detections) == 0:
            return frame
        frame = self.box_annotator.annotate(scene=frame, detections=detections)
        if labels is not None and len(labels) == len(detections):
            frame = self.label_annotator.annotate(
                scene=frame, detections=detections, labels=labels
            )
        return frame


class TrackingAnnotator(BaseAnnotator):
    """Rysuje tracking boxy + labele + ślady (trace)."""
    def __init__(self):
        color = sv.Color.RED
        self.box_annotator = sv.BoxAnnotator(color=color, thickness=2)
        self.label_annotator = sv.LabelAnnotator(
            text_color=color, text_scale=0.6, text_thickness=2
        )
        self.trace_annotator = sv.TraceAnnotator(
            color=color, thickness=2, trace_length=40
        )

    def annotate(self, frame, detections, labels=None):
        if detections is None or len(detections) == 0:
            return frame
        frame = self.box_annotator.annotate(scene=frame, detections=detections)
        if labels is not None and len(labels) == len(detections):
            frame = self.label_annotator.annotate(
                scene=frame, detections=detections, labels=labels
            )
        # trace wymaga tracker_id; bez niego supervision rzuci błąd
        if detections.tracker_id is not None:
            frame = self.trace_annotator.annotate(
                scene=frame, detections=detections
            )
        return frame

    def reset_traces(self):
        if hasattr(self.trace_annotator, "reset"):
            self.trace_annotator.reset()


class ValidationAnnotator(BaseAnnotator):
    """Rysuje wyniki walidacji parkowania – kolor zależy od klasy."""
    _PALETTE = sv.ColorPalette.from_hex([
        "#00FF00",  # 0 poprawne
        "#FF0000",  # 1 niepoprawne
        "#FFFF00",  # 2 inne
    ])
    _LABEL_TO_CLASS = (
        ("Poprawne parkowanie",    0),
        ("Niepoprawne parkowanie", 1),
    )
    _DEFAULT_CLASS_ID = 2

    def __init__(self):
        self.box_annotator = sv.BoxAnnotator(
            color=self._PALETTE,
            thickness=2,
            color_lookup=sv.ColorLookup.CLASS,
        )
        self.label_annotator = sv.LabelAnnotator(
            text_color=self._PALETTE,
            text_scale=0.6,
            text_thickness=2,
            color_lookup=sv.ColorLookup.CLASS,
        )

    def _classify(self, labels, n: int) -> np.ndarray:
        """Zwraca class_id o długości n; przy braku/niezgodności – same 'inne'."""
        if labels is None or len(labels) != n:
            return np.full(n, self._DEFAULT_CLASS_ID, dtype=int)
        ids = np.empty(n, dtype=int)
        for i, label in enumerate(labels):
            if label is None:
                ids[i] = self._DEFAULT_CLASS_ID
                continue
            for fragment, cid in self._LABEL_TO_CLASS:
                if fragment in label:
                    ids[i] = cid
                    break
            else:
                ids[i] = self._DEFAULT_CLASS_ID
        return ids

    def annotate(self, frame, detections, labels=None):
        det = sv.Detections(
            xyxy=detections.xyxy,
            mask=detections.mask,
            confidence=detections.confidence,
            class_id=self._classify(labels, len(detections)),
            tracker_id=detections.tracker_id,
            data=detections.data,
        )
        if detections is None or len(detections) == 0:
            return frame

        det.class_id = self._classify(labels, len(det))

        out = frame.copy()
        out = self.box_annotator.annotate(scene=out, detections=det)
        if labels is not None and len(labels) == len(det):
            out = self.label_annotator.annotate(
                scene=out, detections=det, labels=labels
            )
        return out