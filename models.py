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
        self.load_models_from_dir(models_det_dir_park_slot, self.models_det_cars_spot)


    def load_models_from_dir(self, directory: str, target_list: list):
        """Uniwersalna metoda do wczytywania plików .pt z wskazanego katalogu."""
        if not os.path.exists(directory):
            return  # Zabezpieczenie, gdyby katalog jeszcze nie istniał
            
        for file_name in os.listdir(directory):
            if file_name.endswith('.pt'):
                target_list.append(file_name)

    def load_det_models(self):
        models = os.listdir(models_dir)
        for model in models:
            if model.endswith('.pt'):
                self.det_models.append(model)


    def process_frame(self, frame):
        


      return frame#processed_frame