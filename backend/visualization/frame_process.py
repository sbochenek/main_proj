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

    visualization_options_changed = pyqtSignal(bool, bool, bool, bool, bool)

    def __init__(self, yolo_detection, rf_detections, tracking, predictions, park_validator):
        super().__init__()
        self.yolo_det_annotator = CarDetectionAnnotator()
        self.rf_det_annotator = CarDetectionAnnotator()
        self.park_annotator = ParkDetectionAnnotator()
        self.tracker_annotator = TrackingAnnotator()
        # self.predictions_annotator = Annotator()
        self.validation_annotator = ValidationAnnotator()
        self.prediction_annotator = PredictionAnnotator()
        
        self.draw_car_detection = False
        self.draw_park_detection = False
        self.draw_tracking = False
        self.draw_validation = False
        self.draw_predictions = False
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
        
        pred_detections, pred_labels = None, None

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
                if track_detections is not None:
                    parked_cars_det_validation, validation_labels = self.park_validator.validate(track_detections, park_detection_results, True)
                else:
                    parked_cars_det_validation, validation_labels = self.park_validator.validate(
                        car_detection_results, park_detection_results, False)
            
            #  Predykcja
            if self.tracking.loaded_tracker and self.draw_predictions:
                pred_detections, pred_labels = self.predictions.predict(track_detections, car_names)

            # 4. Wizualizacja
            processed_frame = self.process_visualization( frame,
                car_detection_results, car_detection_labels,
                park_detection_results, park_detection_labels,
                track_detections, track_labels,
                validation_labels, parked_cars_det_validation,
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

            if self.draw_predictions:
                frame = self.prediction_annotator.annotate(frame, self.predictions.trajectories, detections=track_detections)

        except Exception as exc:
            self.error_occurred.emit(str(exc))
        finally:
            return frame

    def set_visualization_options(self, draw_car_detection: bool, draw_park_detection: bool, draw_tracking: bool, draw_validation: bool, draw_prediciotn: bool):
        self.draw_car_detection = draw_car_detection
        self.draw_park_detection = draw_park_detection
        self.draw_tracking = draw_tracking
        self.draw_validation = draw_validation
        self.draw_predictions = draw_prediciotn




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
    """Rysuje wyniki walidacji parkowania. Kolor wynika wyłącznie z tekstu etykiety."""

    # Kolejność jest istotna: "Niepoprawne" musi być sprawdzone przed "Poprawne",
    # bo "Niepoprawne parkowanie" zawiera fragment "poprawne parkowanie".
    # Porównanie jest bez rozróżniania wielkości liter, więc wystarczy ta kolejność.
    _LABEL_COLORS = (
        ("niepoprawne parkowanie", (0, 0, 255)),     # czerwony (BGR)
        ("poprawne parkowanie",    (0, 200, 0)),     # zielony
        ("w ruchu",                (221, 83, 8)),    # niebieski (#0853DD w BGR)
    )
    _DEFAULT_COLOR = (0, 215, 255)                   # żółty/bursztynowy dla reszty

    def __init__(self, thickness: int = 2, text_scale: float = 0.6, text_thickness: int = 2):
        self.thickness = thickness
        self.text_scale = text_scale
        self.text_thickness = text_thickness

    def _color_for(self, label):
        if not label:
            return self._DEFAULT_COLOR
        low = label.lower()
        for fragment, color in self._LABEL_COLORS:
            if fragment in low:
                return color
        return self._DEFAULT_COLOR

    @staticmethod
    def _text_color(bg):
        # czarny tekst na jasnym tle, biały na ciemnym (luminancja BGR)
        b, g, r = bg
        return (0, 0, 0) if (0.114 * b + 0.587 * g + 0.299 * r) > 150 else (255, 255, 255)

    def annotate(self, frame, detections, labels=None):
        if detections is None or len(detections) == 0:
            return frame

        out = frame.copy()
        h, w = out.shape[:2]
        font = cv2.FONT_HERSHEY_SIMPLEX
        use_labels = labels is not None and len(labels) == len(detections)

        for i, box in enumerate(detections.xyxy):
            label = labels[i] if use_labels else None
            color = self._color_for(label)

            x1, y1, x2, y2 = (int(v) for v in box)
            cv2.rectangle(out, (x1, y1), (x2, y2), color, self.thickness)

            if not label:
                continue

            (tw, th), baseline = cv2.getTextSize(label, font, self.text_scale, self.text_thickness)
            pad = 4
            # etykieta nad ramką; jeśli brakuje miejsca u góry, pod górną krawędzią
            top = y1 - th - baseline - 2 * pad
            if top < 0:
                top = y1
            bottom = top + th + baseline + 2 * pad
            right = min(x1 + tw + 2 * pad, w)

            cv2.rectangle(out, (x1, top), (right, bottom), color, -1)
            cv2.putText(
                out, label, (x1 + pad, bottom - baseline - pad),
                font, self.text_scale, self._text_color(color),
                self.text_thickness, cv2.LINE_AA,
            )
        return out


class PredictionAnnotator(BaseAnnotator):
    """Rysuje tylko zielone linie przewidywanej trajektorii."""
    def __init__(self, thickness: int = 2):
        self.color_bgr = (0, 255, 0)   # OpenCV używa BGR: zielony
        self.thickness = thickness

    def annotate(self, frame, trajectories, detections=None, labels=None):
        """
        trajectories: dict {track_id: ndarray (N, 2)} z Predictions.trajectories
        detections:   opcjonalnie sv.Detections z trackera. Gdy podane, linia
                      zaczyna się w środku aktualnego boxa danego obiektu.
        """
        if not trajectories:
            return frame

        # aktualne środki obiektów (początek linii)
        starts = {}
        if detections is not None and detections.tracker_id is not None:
            for box, tid in zip(detections.xyxy, detections.tracker_id):
                starts[int(tid)] = np.array(
                    [(box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0]
                )

        h, w = frame.shape[:2]
        for tid, pts in trajectories.items():
            if pts is None or len(pts) == 0:
                continue
            pts = np.asarray(pts, dtype=np.float32)
            if tid in starts:
                pts = np.vstack([starts[tid], pts])
            if len(pts) < 2:
                continue

            # ograniczenie do obrazu, żeby cv2 nie dostał wartości spoza int32
            pts[:, 0] = np.clip(pts[:, 0], -w, 2 * w)
            pts[:, 1] = np.clip(pts[:, 1], -h, 2 * h)

            cv2.polylines(
                frame,
                [pts.astype(np.int32).reshape(-1, 1, 2)],
                isClosed=False,
                color=self.color_bgr,
                thickness=self.thickness,
                lineType=cv2.LINE_AA,
            )
        return frame