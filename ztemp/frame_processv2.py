# main_app\backend\visualization\frame_process.py
import supervision as sv
from PyQt5.QtCore import QObject, pyqtSignal,  pyqtSlot
import cv2

class FrameProcessor():

    def __init__(self, yolo_detection, tracking, predictions):
        super().__init__()

        self.yolo_detection = yolo_detection
        self.tracking = tracking
        self.predictions = predictions

    def process_frame(self, frame):
        
        # 1. Detekcja
        car_detection_results = self.yolo_detection.detect_cars(frame)
        park_detection_results = self.yolo_detection.detect_park_slot(frame)
        # # 2. Tracking
        detections, labels = self.tracking.track_cars(car_detection_results)

        # # 3. Predykcja
        # prediction_results = self.predictions.process(
        #     tracking_results
        # )

        # 4. Wizualizacja
        processed_frame = self.process_visualization(
            frame,
            car_detection_results,
            park_detection_results,
            detections,
            labels
        )

        return processed_frame
        
    def process_visualization(
        self,
        frame,
        car_detection_results,
        park_detection_results,
        track_detections,
        track_labels
    ):

        if park_detection_results:
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
        elif track_detections and track_labels:
            annotated_frame = self.box_annotator.annotate(
                scene=frame.copy(),
                detections=track_detections
            )

            annotated_frame = self.label_annotator.annotate(
                scene=annotated_frame,
                detections=track_detections,
                labels=track_labels
            )

            annotated_frame = self.trace_annotator.annotate(
                scene=annotated_frame,
                detections=track_detections
            )
                # Tutaj umieść swoją logikę rysowania
                # bounding boxów, ID, trajektorii i predykcji.
            return annotated_frame
        elif car_detection_results:
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
        return frame

class Annotator():
  def __init__(self):
    self.box_annotator = sv.BoxAnnotator()
    self.label_annotator = sv.LabelAnnotator()
    self.trace_annotator = sv.TraceAnnotator()