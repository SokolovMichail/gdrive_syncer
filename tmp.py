from src.synchronizer import Synchronizer

FOLDER = "/home/sokolov/KeePassXC"
GDRIVE_FOLDER = "experiment_folder"

synchronizer = Synchronizer()
synchronizer.synchronize()

print("1")