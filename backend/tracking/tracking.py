from trackers import (
    ByteTrackTracker,
    BoTSORTTracker,
    OCSORTTracker,
    SORTTracker,
)
from enum import Enum
import supervision as sv

class TrackerAlg(Enum):
    SORTTracker = "SORTTracker"
    OCSORTTracker = "OCSORTTracker"
    BoTSORTTracker = "BoTSORTTracker"
    ByteTrack = "ByteTrackTracker"

class Tracking_algorithms():
    
  def __init__(self):
      self.trackers = TrackerAlg
      self.loaded_tracker = None
      self.is_tracking_enabled = False

      self.ByteTrack_config = {'lost_track_buffer':30,
          'frame_rate':30.0,
         'track_activation_threshold':0.7,
          'minimum_consecutive_frames':2,
          'minimum_iou_threshold':0.1,
          'high_conf_det_threshold':0.6
          }
      
      self.BoTSORTTracker_config = {
        "lost_track_buffer": 30,
        "frame_rate": 30.0,
        "track_activation_threshold": 0.7,
        "minimum_consecutive_frames": 2,
        "minimum_iou_threshold_first_assoc": 0.2,
        "minimum_iou_threshold_second_assoc": 0.5,
        "minimum_iou_threshold_unconfirmed_assoc": 0.3,
        "high_conf_det_threshold": 0.6,
        "enable_cmc": True,  # kompensacja ruchu kamery
        "cmc_method": "sparseOptFlow",  # "sift" "sparseOptFlow" "ecc"
        "cmc_downscale": 2,
        "instant_first_frame_activation": True,
      }

      self.OCSORTTracker_config = {
        "lost_track_buffer": 30,
        "frame_rate": 30.0,
        "minimum_consecutive_frames": 3,
        "minimum_iou_threshold": 0.3,
        "direction_consistency_weight": 0.2,
        "high_conf_det_threshold": 0.6,
        "delta_t": 3,
      }

      self.SORTTracker_config = {
        "lost_track_buffer": 30,
        "frame_rate": 30.0,
        "track_activation_threshold": 70,
        "minimum_consecutive_frames": 3,
        "minimum_iou_threshold": 0.3,
      }

      self.ByteTrack = ByteTrackTracker(**self.ByteTrack_config)
      self.BoTSORTTracker = BoTSORTTracker(**self.BoTSORTTracker_config)
      self.OCSORTTracker = OCSORTTracker(**self.OCSORTTracker_config)
      self.SORTTracker = SORTTracker(**self.SORTTracker_config)

  def track_cars(self, result):
    if self.loaded_tracker is not None:
      detections = sv.Detections.from_ultralytics(result)

      # 3. Przypisanie identyfikatorów
      detections = self.loaded_tracker.update(detections)
      # 4. Pominięcie obiektów bez przypisanego ID
      detections = detections[detections.tracker_id != -1]

      # 5. Przygotowanie etykiet: ID + nazwa klasy
      labels = [
          f"ID {tracker_id} {result.names[class_id]}"
          for tracker_id, class_id in zip(
              detections.tracker_id,
              detections.class_id
          )
      ]
      return detections, labels
    else: 
      return None, None


  def get_config(self, alg: TrackerAlg) -> dict:
    mapping = {
        TrackerAlg.ByteTrack:       self.ByteTrack_config,
        TrackerAlg.BoTSORTTracker:  self.BoTSORTTracker_config,
        TrackerAlg.OCSORTTracker:   self.OCSORTTracker_config,
        TrackerAlg.SORTTracker:     self.SORTTracker_config,
    }
    return mapping[alg]
  
  def update_config(self, tracker_name: str, new_params: dict):
    alg = TrackerAlg(tracker_name)

    if alg == TrackerAlg.ByteTrack:
        self.ByteTrack_config.update(new_params)
        self.ByteTrack = ByteTrackTracker(**self.ByteTrack_config)
    elif alg == TrackerAlg.BoTSORTTracker:
        self.BoTSORTTracker_config.update(new_params)
        self.BoTSORTTracker = BoTSORTTracker(**self.BoTSORTTracker_config)
    elif alg == TrackerAlg.OCSORTTracker:
        self.OCSORTTracker_config.update(new_params)
        self.OCSORTTracker = OCSORTTracker(**self.OCSORTTracker_config)
    elif alg == TrackerAlg.SORTTracker:
        self.SORTTracker_config.update(new_params)
        self.SORTTracker = SORTTracker(**self.SORTTracker_config)

  def set_track_alg(self, algtype):
    self.reset_track_alg()
    self.is_tracking_enabled = True
    if algtype == TrackerAlg.ByteTrack.value:
        self.loaded_tracker = self.ByteTrack
    elif algtype == TrackerAlg.BoTSORTTracker.value:
        self.loaded_tracker = self.BoTSORTTracker
    elif algtype == TrackerAlg.OCSORTTracker.value:
        self.loaded_tracker = self.OCSORTTracker
    elif algtype == TrackerAlg.SORTTracker.value:
        self.loaded_tracker = self.SORTTracker
    else:
        self.loaded_tracker = None
        print(f'nieznany typ trackera {algtype}')
        self.is_tracking_enabled = False
    print(f"ustawiono tracker: {self.loaded_tracker.__class__.__name__}"
          f"tracking enabled?: {self.is_tracking_enabled}")

  def reset_track_alg(self):
    if self.loaded_tracker is not None:
        self.loaded_tracker.reset()
        print("zresetowano dane trackera")
    self.loaded_tracker = None
    self.is_tracking_enabled = False

  def deactivate_tracking(self):
    print("wylaczanie trackowania")
    self.reset_track_alg()
    self.is_tracking_enabled = False
    self.loaded_tracker = None

  def change_tracker(self, algtype):
    print(f"aktywny tracker: {self.loaded_tracker.__class__.__name__ }"
          f"zmiana na tracker {algtype}")
    if self.loaded_tracker.__class__.__name__ == algtype:
      self.deactivate_tracking()
    else:
       self.set_track_alg(algtype)