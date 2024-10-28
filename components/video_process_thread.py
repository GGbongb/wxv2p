import cv2
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal
import logging
import os

class VideoProcessThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(list)
    log_message = pyqtSignal(str)

    def __init__(self, video_path):
        super().__init__()
        self.video_path = video_path
        self.setup_logging()
        self.debug_output_dir = "debug_output"
        self.repeat_region_dir = "repeat_regions"
        os.makedirs(self.debug_output_dir, exist_ok=True)
        os.makedirs(self.repeat_region_dir, exist_ok=True)
        
        self.fixed_top_height = 120
        self.fixed_bottom_height = 70
        self.repeat_check_height = 120  # 重复检测区域的高度
        self.similarity_threshold = 0.80  # 相似度阈值
        self.consecutive_frames_threshold = 3  # 连续相似帧数阈值

    def setup_logging(self):
        self.logger = logging.getLogger('VideoProcessThread')
        self.logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def log(self, message):
        self.logger.info(message)
        self.log_message.emit(message)

    def run(self):
        cap = cv2.VideoCapture(self.video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.log(f"Total frames: {total_frames}")

        frames = []
        last_repeat_region = None


        for i in range(total_frames):
            ret, frame = cap.read()
            if not ret:
                self.log(f"Failed to read frame {i}")
                break

            if len(frames) == 0:
                frames.append(frame)
                last_repeat_region = self.get_repeat_region(frame)
                self.save_debug_frame(frame, i, "First", self.fixed_top_height, self.fixed_bottom_height)
                self.save_repeat_region(last_repeat_region, i, "First_Repeat")
                continue

            current_top_region = frame[self.fixed_top_height:self.fixed_top_height+self.repeat_check_height]
            similarity, comparison_image = self.check_similarity(last_repeat_region, current_top_region)
            
            is_similar = similarity >= self.similarity_threshold
            status = f"Similar_{similarity:.4f}" if is_similar else f"Different_{similarity:.4f}"
            self.save_comparison_image(comparison_image, i, status)
            
            if is_similar:
                frames.append(frame)
                last_repeat_region = self.get_repeat_region(frame)
                self.log(f"Added new frame {len(frames)}, similarity: {similarity:.4f}")
                self.save_debug_frame(frame, i, f"Frame_{len(frames)}", self.fixed_top_height, self.fixed_bottom_height)
                self.save_repeat_region(last_repeat_region, i, f"NewRepeat_{len(frames)}")
            else:
                self.save_debug_frame(frame, i, f"Skipped_{similarity:.4f}", self.fixed_top_height, self.fixed_bottom_height)
 

            self.progress.emit(int((i + 1) / total_frames * 100))

            if i > 200 :
                break

        cap.release()
        self.log(f"Processing completed. Total frames captured: {len(frames)}")
        self.finished.emit(frames)

    def get_repeat_region(self, frame):
        return frame[-self.fixed_bottom_height-self.repeat_check_height:-self.fixed_bottom_height]

    def check_similarity(self, repeat_region, current_top_region):
        repeat_region_gray = cv2.cvtColor(repeat_region, cv2.COLOR_BGR2GRAY)
        current_top_region_gray = cv2.cvtColor(current_top_region, cv2.COLOR_BGR2GRAY)
        
        result = cv2.matchTemplate(current_top_region_gray, repeat_region_gray, cv2.TM_CCOEFF_NORMED)
        similarity = np.max(result)
        
        comparison_image = np.hstack((repeat_region, current_top_region))
        return similarity, comparison_image

    def save_debug_frame(self, frame, frame_number, status, fixed_top_height, fixed_bottom_height):
        debug_frame = frame.copy()
        
        cv2.line(debug_frame, (0, fixed_top_height), (debug_frame.shape[1], fixed_top_height), (0, 255, 0), 2)
        cv2.line(debug_frame, (0, debug_frame.shape[0] - fixed_bottom_height), (debug_frame.shape[1], debug_frame.shape[0] - fixed_bottom_height), (0, 255, 0), 2)
        
        cv2.rectangle(debug_frame, (0, fixed_top_height), (debug_frame.shape[1], fixed_top_height + self.repeat_check_height), (255, 0, 0), 2)
        cv2.rectangle(debug_frame, (0, debug_frame.shape[0] - fixed_bottom_height - self.repeat_check_height), (debug_frame.shape[1], debug_frame.shape[0] - fixed_bottom_height), (255, 0, 0), 2)
        
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(debug_frame, status, (10, 30), font, 1, (0, 0, 255), 2, cv2.LINE_AA)
        
        filename = f"{self.debug_output_dir}/frame_{frame_number:04d}_{status}.jpg"
        cv2.imwrite(filename, debug_frame)
        self.log(f"Saved debug frame: {filename}")

    def save_repeat_region(self, repeat_region, frame_number, status):
        filename = f"{self.repeat_region_dir}/repeat_region_{frame_number:04d}_{status}.jpg"
        cv2.imwrite(filename, repeat_region)
        self.log(f"Saved repeat region: {filename}")

    def save_comparison_image(self, comparison_image, frame_number, status):
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(comparison_image, "Last Repeat", (10, 30), font, 1, (0, 255, 0), 2, cv2.LINE_AA)
        cv2.putText(comparison_image, "Current Top", (comparison_image.shape[1]//2 + 10, 30), font, 1, (0, 255, 0), 2, cv2.LINE_AA)
        cv2.putText(comparison_image, status, (10, comparison_image.shape[0] - 10), font, 1, (0, 0, 255), 2, cv2.LINE_AA)
        
        filename = f"{self.repeat_region_dir}/comparison_{frame_number:04d}_{status}.jpg"
        cv2.imwrite(filename, comparison_image)
        self.log(f"Saved comparison image: {filename}")
