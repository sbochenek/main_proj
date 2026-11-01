# models.py
import os
from enum import Enum

from ultralytics.trackers.utils.kalman_filter import KalmanFilterXYAH
import numpy as np

import onnxruntime as ort
print("ONNX Runtime:", ort.__version__)

import cv2
print("OpenCV OK")

from ultralytics import YOLO
print("Ultralytics OK")

import supervision as sv
print("Supervision OK")



class Predictions():
    def __init__(self):
        self.kf = KalmanFilterXYAH()
        self.next_track_id = 0
        self.tracks = {}
        self.box_annotator = sv.BoxAnnotator()
        self.label_annotator = sv.LabelAnnotator()
        self.trace_annotator = sv.TraceAnnotator()
    def pred(self, frame, results):
            print('wywolanie funkcji pred')
            
            detections_list = []

            # 1. Predykcja Kalmana dla wszystkich istniejących śladów
            for track_id, track in self.tracks.items():
                track["mean"], track["covariance"] = self.kf.predict(
                    track["mean"], track["covariance"]
                )

            # 2. Odczyt detekcji z YOLO dla bieżącej klatki i budowanie pomiarów dla Kalmana
            yolo_detections = []
            if results.boxes is not None and len(results.boxes) > 0:
                boxes = results.boxes.xyxy.cpu().numpy()
                classes = results.boxes.cls.cpu().numpy()
                confidences = results.boxes.conf.cpu().numpy()
                
                for box, cls, conf in zip(boxes, classes, confidences):
                    x1, y1, x2, y2 = box
                    w = x2 - x1
                    h = y2 - y1
                    x_center = x1 + w / 2.0
                    y_center = y1 + h / 2.0
                    aspect_ratio = w / float(h) if h > 0 else 0

                    measurement = np.array([x_center, y_center, aspect_ratio, h])
                    yolo_detections.append({
                        "measurement": measurement,
                        "cls": int(cls),
                        "conf": float(conf)
                    })

            # 3. Asocjacja i aktualizacja filtrów Kalmana
            assigned_track_ids = set()
            
            # Listy do zbudowania sv.Detections dla Supervision
            xyxy_list = []
            tracker_id_list = []
            confidence_list = []
            class_id_list = []

            for item in yolo_detections:
                det = item["measurement"]
                matched_id = None
                min_dist = float("inf")
                
                for track_id, track in self.tracks.items():
                    if track_id in assigned_track_ids:
                        continue
                    
                    dist = np.linalg.norm(track["mean"][:2] - det[:2])
                    if dist < 50.0 and dist < min_dist:
                        min_dist = dist
                        matched_id = track_id

                if matched_id is not None:
                    # Aktualizacja istniejącego śladu
                    self.tracks[matched_id]["mean"], self.tracks[matched_id]["covariance"] = self.kf.update(
                        self.tracks[matched_id]["mean"], self.tracks[matched_id]["covariance"], det
                    )
                    assigned_track_ids.add(matched_id)
                    current_id = matched_id
                    track_to_draw = self.tracks[matched_id]["mean"]
                else:
                    # Inicjalizacja nowego śladu
                    mean, covariance = self.kf.initiate(det)
                    self.tracks[self.next_track_id] = {"mean": mean, "covariance": covariance}
                    current_id = self.next_track_id
                    track_to_draw = mean
                    assigned_track_ids.add(self.next_track_id)
                    self.next_track_id += 1

                # Obliczenie współrzędnych xyxy z uaktualnionego stanu Kalmana
                x, y, a, h = track_to_draw[:4]
                w = a * h
                x1 = int(x - w / 2)
                y1 = int(y - h / 2)
                x2 = int(x + w / 2)
                y2 = int(y + h / 2)

                xyxy_list.append([x1, y1, x2, y2])
                tracker_id_list.append(current_id)
                confidence_list.append(item["conf"])
                class_id_list.append(item["cls"])

            # 4. Jeśli mamy ślady, tworzymy obiekt sv.Detections i rysujemy adnotatorami
            if len(xyxy_list) > 0:
                detections = sv.Detections(
                    xyxy=np.array(xyxy_list, dtype=np.float32),
                    confidence=np.array(confidence_list, dtype=np.float32),
                    class_id=np.array(class_id_list, dtype=int),
                    tracker_id=np.array(tracker_id_list, dtype=int)
                )

                # Przygotowanie etykiet (ID + nazwa klasy z modelu YOLO)
                labels = [
                    f"ID {tid} {results.names[cid]}"
                    for tid, cid in zip(detections.tracker_id, detections.class_id)
                ]

                # Rysowanie za pomocą Supervision Annotators
                annotated_frame = frame.copy()
                annotated_frame = self.box_annotator.annotate(scene=annotated_frame, detections=detections)
                annotated_frame = self.label_annotator.annotate(scene=annotated_frame, detections=detections, labels=labels)
                annotated_frame = self.trace_annotator.annotate(scene=annotated_frame, detections=detections)

                for tid in tracker_id_list:
                    if tid in self.tracks:
                        # Pobieramy np. 15 klatek w przód
                        future_steps = self.predict_future(tid, future_frames=20)
                        
                        points = []
                        for step in future_steps:
                            # Przeliczamy środki przewidywanych prostokątów na punkty na ekranie
                            fx = int(step["x"])
                            fy = int(step["y"])
                            points.append((fx, fy))
                        
                        # Rysujemy linie łączące punkty przyszłej trajektorii
                        for i in range(len(points) - 1):
                            cv2.line(annotated_frame, points[i], points[i+1], (0, 255, 255), 2)  # Żółta linia
                            cv2.circle(annotated_frame, points[i+1], 3, (0, 0, 255), -1)        # Czerwone kropki

                return annotated_frame
                
            return frame

    def predict_future(self, track_id, future_frames=10):

        track = self.tracks[track_id]

        mean = track["mean"].copy()
        covariance = track["covariance"].copy()

        predictions = []

        for i in range(future_frames):

            mean, covariance = self.kf.predict(
                mean, covariance
            )

            x, y, a, h = mean[:4]

            w = a * h

            predictions.append({
                "frame": i + 1,
                "x": x,
                "y": y,
                "width": w,
                "height": h
            })

