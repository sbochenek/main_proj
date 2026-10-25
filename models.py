import os



root = os.getcwd()
models_det_dir_park_slot = os.path.join(root, "models\\park_det_models")
models_dir = os.path.join(root, "models")

class Models():
    def __init__(self):
        self.models_det_cars_spot = []
        self.det_models = []
        self.track_models = []
        self.load_det_models()
        self.load_models_det_park_spot()

    def load_det_models(self):
        models = os.listdir(models_dir)
        for model in models:
            if model.endswith('.pt'):
                self.det_models.append(model)

    def load_models_det_park_spot(self):
        models = os.listdir(models_det_dir_park_slot)
        for model in models:
            if model.endswith('.pt'):
                self.models_det_cars_spot.append(model)


    def process_frame(self, frame):
        


      return frame#processed_frame