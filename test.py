from trackers import (
    ByteTrackTracker,
    BoTSORTTracker,
    OCSORTTracker,
    SORTTracker,
)
byte_track_config = {'lost_track_buffer':30,
          'frame_rate':30.0,
         'track_activation_threshold':0.7,
          'minimum_consecutive_frames':2,
          'minimum_iou_threshold':0.1,
          'high_conf_det_threshold':0.6}

ByteTrackTracker(**byte_track_config)


print('ok')