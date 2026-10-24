import os



root = os.getcwd()
models_dir = os.path.join(root, "models")

class Models():
    def __init__(self):
        self.det_models = []
        self.track_models = []
        self.load_det_models()

    def load_det_models(self):
        models = os.listdir(models_dir)
        for model in models:
            if model.endswith('.pt'):
                self.det_models.append(model)