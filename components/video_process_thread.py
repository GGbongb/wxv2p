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
        self.repeat_check_height = 120  # 实际显示的重复检测区域高度
        self.extended_check_height = 240  # 扩展的检测区域高度（2倍）
        self.rough_similarity_threshold = 0.75  # 大区域的相似度阈值（可以稍微降低）
        self.fine_similarity_threshold = 0.80  # 小区域的相似度阈值

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
                last_repeat_region = self.get_repeat_region(frame, extended=True)
                self.save_debug_frame(frame, i, "First", self.fixed_top_height, self.fixed_bottom_height)
                self.save_repeat_region(last_repeat_region[:self.repeat_check_height], i, "First_Repeat")
                continue

            current_top_region = self.get_top_region(frame, extended=True)
            extended_similarity, actual_similarity, comparison_image = self.check_similarity(last_repeat_region, current_top_region)
            
            status = f"Extended_{extended_similarity:.4f}_Actual_{actual_similarity:.4f}"
            self.save_comparison_image(comparison_image, i, status)
            
            if extended_similarity >= self.rough_similarity_threshold:
                frames.append(frame)
                last_repeat_region = self.get_repeat_region(frame, extended=True)
                self.log(f"Added new frame {len(frames)}, similarities: {status}")
                self.save_debug_frame(frame, i, f"Frame_{len(frames)}", self.fixed_top_height, self.fixed_bottom_height)
                self.save_repeat_region(last_repeat_region[:self.repeat_check_height], i, f"NewRepeat_{len(frames)}")
            else:
                self.save_debug_frame(frame, i, f"Skipped_{status}", self.fixed_top_height, self.fixed_bottom_height)

            self.progress.emit(int((i + 1) / total_frames * 100))

        cap.release()
        self.log(f"Processing completed. Total frames captured: {len(frames)}")
        self.finished.emit(frames)

    def get_repeat_region(self, frame, extended=False):
        height = self.extended_check_height if extended else self.repeat_check_height
        return frame[-self.fixed_bottom_height-height:-self.fixed_bottom_height]

    def get_top_region(self, frame, extended=False):
        height = self.extended_check_height if extended else self.repeat_check_height
        return frame[self.fixed_top_height:self.fixed_top_height+height]


    def check_similarity(self, repeat_region, current_top_region):
        # 保存扩展区域的引用，供save_comparison_image使用
        self.last_extended_repeat = repeat_region
        self.current_extended_top = current_top_region
        
        # 转换为灰度图像
        extended_repeat_gray = cv2.cvtColor(repeat_region, cv2.COLOR_BGR2GRAY)
        extended_current_gray = cv2.cvtColor(current_top_region, cv2.COLOR_BGR2GRAY)
        
        # 计算扩展区域的相似度
        result = cv2.matchTemplate(extended_current_gray, extended_repeat_gray, cv2.TM_CCOEFF_NORMED)
        extended_similarity = np.max(result)
        
        # 获取实际显示的重复区域
        actual_repeat = repeat_region[:self.repeat_check_height]
        actual_current = current_top_region[:self.repeat_check_height]
        
        # 计算实际区域的相似度
        actual_repeat_gray = cv2.cvtColor(actual_repeat, cv2.COLOR_BGR2GRAY)
        actual_current_gray = cv2.cvtColor(actual_current, cv2.COLOR_BGR2GRAY)
        result = cv2.matchTemplate(actual_current_gray, actual_repeat_gray, cv2.TM_CCOEFF_NORMED)
        actual_similarity = np.max(result)
        
        # 创建对比图像（只显示实际的重复区域）
        comparison_image = np.hstack((actual_repeat, actual_current))
        
        return extended_similarity, actual_similarity, comparison_image
    
    def save_debug_frame(self, frame, frame_number, status, fixed_top_height, fixed_bottom_height):
        debug_frame = frame.copy()
        
        # 绘制固定区域的线
        cv2.line(debug_frame, (0, fixed_top_height), (debug_frame.shape[1], fixed_top_height), (0, 255, 0), 2)
        cv2.line(debug_frame, (0, debug_frame.shape[0] - fixed_bottom_height), (debug_frame.shape[1], debug_frame.shape[0] - fixed_bottom_height), (0, 255, 0), 2)
        
        # 绘制实际重复检测区域（蓝色）
        cv2.rectangle(debug_frame, 
                    (0, fixed_top_height), 
                    (debug_frame.shape[1], fixed_top_height + self.repeat_check_height), 
                    (255, 0, 0), 2)
        cv2.rectangle(debug_frame, 
                    (0, debug_frame.shape[0] - fixed_bottom_height - self.repeat_check_height), 
                    (debug_frame.shape[1], debug_frame.shape[0] - fixed_bottom_height), 
                    (255, 0, 0), 2)
        
        # 绘制扩展检测区域（红色）
        cv2.rectangle(debug_frame, 
                    (0, fixed_top_height), 
                    (debug_frame.shape[1], fixed_top_height + self.extended_check_height), 
                    (0, 0, 255), 2)
        cv2.rectangle(debug_frame, 
                    (0, debug_frame.shape[0] - fixed_bottom_height - self.extended_check_height), 
                    (debug_frame.shape[1], debug_frame.shape[0] - fixed_bottom_height), 
                    (0, 0, 255), 2)
        
        # 添加标注文字
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(debug_frame, "Actual Region", (10, fixed_top_height - 10), font, 0.7, (255, 0, 0), 2)
        cv2.putText(debug_frame, "Extended Region", (10, fixed_top_height + self.repeat_check_height + 20), font, 0.7, (0, 0, 255), 2)
        cv2.putText(debug_frame, status, (10, 30), font, 1, (0, 0, 255), 2, cv2.LINE_AA)
        
        filename = f"{self.debug_output_dir}/frame_{frame_number:04d}_{status}.jpg"
        cv2.imwrite(filename, debug_frame)
        self.log(f"Saved debug frame: {filename}")




    def save_repeat_region(self, repeat_region, frame_number, status):
        filename = f"{self.repeat_region_dir}/repeat_region_{frame_number:04d}_{status}.jpg"
        cv2.imwrite(filename, repeat_region)
        self.log(f"Saved repeat region: {filename}")

    def save_comparison_image(self, comparison_image, frame_number, status):
        # 创建一个更大的画布来显示两种区域的对比
        extended_height = self.extended_check_height
        actual_height = self.repeat_check_height
        width = comparison_image.shape[1]
        
        # 创建白色背景
        full_comparison = np.ones((extended_height + 50, width, 3), dtype=np.uint8) * 255
        
        # 复制扩展区域图像
        full_comparison[0:extended_height, :width//2] = self.last_extended_repeat
        full_comparison[0:extended_height, width//2:] = self.current_extended_top
        
        # 在扩展区域上标记实际区域的范围（蓝色矩形）
        cv2.rectangle(full_comparison, 
                    (0, 0), 
                    (width//2, actual_height), 
                    (255, 0, 0), 2)
        cv2.rectangle(full_comparison, 
                    (width//2, 0), 
                    (width, actual_height), 
                    (255, 0, 0), 2)
        
        font = cv2.FONT_HERSHEY_SIMPLEX
        # 添加标题
        cv2.putText(full_comparison, "Last Repeat", (10, 30), font, 1, (0, 255, 0), 2)
        cv2.putText(full_comparison, "Current Top", (width//2 + 10, 30), font, 1, (0, 255, 0), 2)
        
        # 添加区域标注
        cv2.putText(full_comparison, "Actual", (10, actual_height - 5), font, 0.7, (255, 0, 0), 2)
        cv2.putText(full_comparison, "Extended", (10, extended_height - 5), font, 0.7, (0, 0, 255), 2)
        
        # 添加相似度信息
        cv2.putText(full_comparison, status, (10, extended_height + 30), font, 0.7, (0, 0, 255), 2)
        
        filename = f"{self.repeat_region_dir}/comparison_{frame_number:04d}_{status}.jpg"
        cv2.imwrite(filename, full_comparison)
        self.log(f"Saved comparison image: {filename}")