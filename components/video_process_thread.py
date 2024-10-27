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
        self.repeat_check_height = 100  # 重复检测区域的高度
        self.similarity_threshold = 1.85  # 降低相似度阈值以增加容忍度
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
        consecutive_similar_frames = 0

        for i in range(total_frames):
            ret, frame = cap.read()
            if not ret:
                self.log(f"Failed to read frame {i}")
                break

            if len(frames) == 0:
                frames.append(frame)
                last_repeat_region = self.get_repeat_region(frame)
                self.save_debug_frame(frame, i, "First", self.fixed_top_height, self.fixed_bottom_height)
                self.save_repeat_region(last_repeat_region, len(frames))
                continue

            current_top_region = frame[self.fixed_top_height:self.fixed_top_height+self.repeat_check_height]
            similarity, _ = self.check_similarity(last_repeat_region, current_top_region)
            
            if similarity >= self.similarity_threshold:
                consecutive_similar_frames += 1
            else:
                consecutive_similar_frames = 0

            if consecutive_similar_frames >= self.consecutive_frames_threshold:
                frames.append(frame)
                last_repeat_region = self.get_repeat_region(frame)
                self.log(f"Added new frame {len(frames)}, similarity: {similarity:.4f}")
                self.save_debug_frame(frame, i, f"Frame_{len(frames)}", self.fixed_top_height, self.fixed_bottom_height)
                self.save_repeat_region(last_repeat_region, len(frames))
                consecutive_similar_frames = 0
            else:
                self.save_debug_frame(frame, i, f"Skipped_{similarity:.4f}", self.fixed_top_height, self.fixed_bottom_height)

            self.progress.emit(int((i + 1) / total_frames * 100))

            if len(frames) > 500:
                break

        cap.release()
        self.log(f"Processing completed. Total frames captured: {len(frames)}")
        self.finished.emit(frames)

    def get_repeat_region(self, frame):
        return frame[-self.fixed_bottom_height-self.repeat_check_height:-self.fixed_bottom_height]

    def check_similarity(self, repeat_region, current_top_region):
        # 转换为灰度图像
        repeat_region_gray = cv2.cvtColor(repeat_region, cv2.COLOR_BGR2GRAY)
        current_top_region_gray = cv2.cvtColor(current_top_region, cv2.COLOR_BGR2GRAY)
        
        # 计算相似度
        result = cv2.matchTemplate(current_top_region_gray, repeat_region_gray, cv2.TM_CCOEFF_NORMED)
        similarity = np.max(result)
        
        return similarity, result

    def save_debug_frame(self, frame, frame_number, status, fixed_top_height, fixed_bottom_height):
        debug_frame = frame.copy()
        
        # 标记固定区域
        cv2.line(debug_frame, (0, fixed_top_height), (debug_frame.shape[1], fixed_top_height), (0, 255, 0), 2)
        cv2.line(debug_frame, (0, debug_frame.shape[0] - fixed_bottom_height), (debug_frame.shape[1], debug_frame.shape[0] - fixed_bottom_height), (0, 255, 0), 2)
        
        # 标记重复检测区域
        cv2.rectangle(debug_frame, (0, fixed_top_height), (debug_frame.shape[1], fixed_top_height + self.repeat_check_height), (255, 0, 0), 2)
        cv2.rectangle(debug_frame, (0, debug_frame.shape[0] - fixed_bottom_height - self.repeat_check_height), (debug_frame.shape[1], debug_frame.shape[0] - fixed_bottom_height), (255, 0, 0), 2)
        
        # 添加状态文字
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(debug_frame, status, (10, 30), font, 1, (0, 0, 255), 2, cv2.LINE_AA)
        
        filename = f"{self.debug_output_dir}/frame_{frame_number:04d}_{status}.jpg"
        cv2.imwrite(filename, debug_frame)
        self.log(f"Saved debug frame: {filename}")

    def save_repeat_region(self, repeat_region, frame_number):
        filename = f"{self.repeat_region_dir}/repeat_region_{frame_number:04d}.jpg"
        cv2.imwrite(filename, repeat_region)
        self.log(f"Saved repeat region: {filename}")
