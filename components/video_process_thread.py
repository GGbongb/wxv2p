import cv2
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal

class VideoProcessThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(list)

    def __init__(self, video_path):
        super().__init__()
        self.video_path = video_path

    def run(self):
        cap = cv2.VideoCapture(self.video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frames = []
        last_frame = None

        for i in range(total_frames):
            ret, frame = cap.read()
            if not ret:
                break

            if last_frame is None or self.frame_difference(last_frame, frame) > 0.1:
                frames.append(frame)
                last_frame = frame

            self.progress.emit(int((i + 1) / total_frames * 100))

        cap.release()
        self.finished.emit(frames)

    def frame_difference(self, frame1, frame2):
        gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
        diff = cv2.absdiff(gray1, gray2)
        return np.mean(diff) / 255.0