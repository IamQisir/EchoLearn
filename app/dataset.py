import os

class Dataset:
    """
    class Dataset is designed for loading the learning_database
    """
    root_path = "database/learning_database/"
    def __init__(self, user_name:str) -> None:
        # create the folder for the specific user
        self.path = self.root_path + f"{user_name}/"
        # name of text and video
        self.text_data = []
        self.video_data = []
    
    def build_dirs(self):
        # build text and video folder for a user
        # this method seems a little meaningless
        try:
            os.makedirs(self.path, exist_ok=False)
        except:
            print("Failed to build the directories!")

    def load_data(self):
        for root, dirs, files in os.walk(self.path):
            for f in files:
                if f.endswith('.txt'):
                    self.text_data.append(f)
                elif f.endswith('.mp4'):
                    self.video_data.append(f)

if __name__ == "__main__":
    dataset = Dataset('qi')
    dataset.load_data()
    print(dataset.text_data, dataset.video_data)