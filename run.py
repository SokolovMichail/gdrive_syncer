from src.synchronizer import Synchronizer

FOLDER = "/home/sokolov/KeePassXC"
GDRIVE_FOLDER = "KeePassFolder"

synchronizer = Synchronizer(GDRIVE_FOLDER,FOLDER)
synchronizer.synchronize()