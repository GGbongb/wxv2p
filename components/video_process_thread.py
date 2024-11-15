import cv2
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal
import logging
import os
from PIL import Image, ImageDraw, ImageFont

class VideoProcessThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(list)
    log_message = pyqtSignal(str)  # 新增信号用于发送日志消息

    def __init__(self, video_path):
        super().__init__()
        self.video_path = video_path
        self.setup_logging()
        self.debug_output_dir = "debug_output"
        os.makedirs(self.debug_output_dir, exist_ok=True)
        
        # 添加可调整的固定区域高度
        self.fixed_top_height = 120  # 您可以手动调整这个值
        self.fixed_bottom_height = 70  # 您可以手动调整这个值

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
        # 使用固定值替代检测
        fixed_top_height, fixed_bottom_height = self.fixed_top_height, self.fixed_bottom_height
        self.log(f"Using fixed top height: {fixed_top_height}, bottom height: {fixed_bottom_height}")
        overlap = 120
        tolerance = 100  # 容忍度，单位为像素

        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        last_content = None
        last_non_empty_content_end = fixed_top_height

        frame_count = 0
        for i in range(total_frames):
            ret, frame = cap.read()
            if not ret:
                self.log(f"Failed to read frame {i}")
                break

            full_frame = frame.copy()
            content_frame = frame[fixed_top_height:-fixed_bottom_height]
            
            self.log(f"Frame {i} - Full size: {full_frame.shape}")
            self.log(f"Frame {i} - Content size: {content_frame.shape}")

            if last_content is None:
                frames.append(full_frame)
                last_non_empty_content_end = self.find_non_empty_content_end(content_frame) + fixed_top_height
                last_content = content_frame.copy()
                self.log(f"Added first frame, content end at: {last_non_empty_content_end}")
                self.save_debug_frame(full_frame, i, "First", fixed_top_height, fixed_bottom_height, last_non_empty_content_end)
                frame_count += 1
            else:
                overlap_region = (last_non_empty_content_end - overlap, last_non_empty_content_end)
                new_content_start = self.find_new_content_start(content_frame, last_content, tolerance)
                self.log(f"Frame {i} - Overlap region: {overlap_region}, New content start: {new_content_start}")
                
                if new_content_start is not None:
                    start_y = max(fixed_top_height, new_content_start + fixed_top_height - overlap)
                    cropped_frame = self.crop_frame(full_frame, start_y)
                    if cropped_frame.shape[0] > fixed_top_height + overlap:
                        frames.append(cropped_frame)
                        new_content_end = self.find_non_empty_content_end(content_frame[new_content_start:]) + new_content_start
                        last_non_empty_content_end = new_content_end + fixed_top_height
                        last_content = content_frame.copy()
                        self.log(f"Added new frame {frame_count + 1}, start_y: {start_y}, content end: {last_non_empty_content_end}")
                        self.save_debug_frame(cropped_frame, i, f"Frame_{frame_count + 1}", fixed_top_height, fixed_bottom_height, last_non_empty_content_end, overlap_region, new_content_start + fixed_top_height)
                        frame_count += 1
                    else:
                        self.log(f"Frame {i} skipped, not enough new content")
                        self.save_debug_frame(full_frame, i, "Skipped_ShortContent", fixed_top_height, fixed_bottom_height, last_non_empty_content_end, overlap_region, new_content_start + fixed_top_height)
                else:
                    self.log(f"Frame {i} skipped, no new content detected")
                    self.save_debug_frame(full_frame, i, "Skipped_NoNewContent", fixed_top_height, fixed_bottom_height, last_non_empty_content_end, overlap_region)

            self.progress.emit(int((i + 1) / total_frames * 100))

            if i >= 300:
                break

        cap.release()
        self.log(f"Processing completed. Total frames captured: {len(frames)}")
        self.finished.emit(frames)

    def find_new_content_start(self, current_frame, last_frame, tolerance):
        diff = cv2.absdiff(current_frame, last_frame)
        gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray_diff, 30, 255, cv2.THRESH_BINARY)
        
        # 使用形态学操作来减少噪声
        kernel = np.ones((5,5), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        
        row_sums = np.sum(thresh, axis=1)
        new_content_rows = np.where(row_sums > thresh.shape[1] * 0.1)[0]  # 10% 的列有变化
        
        if len(new_content_rows) > 0:
            # 找到第一个连续的新内容区域
            for i in range(len(new_content_rows) - 1):
                if new_content_rows[i+1] - new_content_rows[i] > tolerance:
                    return new_content_rows[i]
            return new_content_rows[0]
        return None

    def save_debug_frame(self, frame, frame_number, status, fixed_top_height, fixed_bottom_height, content_end, overlap_region=None, new_content_start=None):
        debug_frame = frame.copy()
        
        # 使用虚线标记固定区域
        cv2.line(debug_frame, (0, fixed_top_height), (debug_frame.shape[1], fixed_top_height), (0, 255, 0), 2, lineType=cv2.LINE_AA, shift=0)
        cv2.line(debug_frame, (0, debug_frame.shape[0] - fixed_bottom_height), (debug_frame.shape[1], debug_frame.shape[0] - fixed_bottom_height), (0, 255, 0), 2, lineType=cv2.LINE_AA, shift=0)
        
        # 标记可变动区域
        cv2.rectangle(debug_frame, (0, fixed_top_height), (debug_frame.shape[1], debug_frame.shape[0] - fixed_bottom_height), (255, 255, 0), 2, lineType=cv2.LINE_AA)
        
        # 标记内容结束位置
        cv2.line(debug_frame, (0, content_end), (debug_frame.shape[1], content_end), (0, 0, 255), 2, lineType=cv2.LINE_AA, shift=0)
        
        # 标记重复区域
        if overlap_region:
            cv2.rectangle(debug_frame, (0, overlap_region[0]), (debug_frame.shape[1], overlap_region[1]), (255, 0, 255), 2, lineType=cv2.LINE_AA)
        
        # 标记新内容开始位置
        if new_content_start:
            cv2.line(debug_frame, (0, new_content_start), (debug_frame.shape[1], new_content_start), (0, 255, 255), 2, lineType=cv2.LINE_AA, shift=0)
        
        # 添加文字说明
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1.0
        font_thickness = 2
        text_color = (255, 255, 255)
        
        def put_centered_text(img, text, y):
            text_size = cv2.getTextSize(text, font, font_scale, font_thickness)[0]
            text_x = (img.shape[1] - text_size[0]) // 2
            text_color = (0, 0, 255)  # 红色，BGR 格式
            cv2.putText(img, text, (text_x, y), font, font_scale, text_color, font_thickness, cv2.LINE_AA)
        
        put_centered_text(debug_frame, "Fixed Top Area", fixed_top_height - 30)
        put_centered_text(debug_frame, "Fixed Bottom Area", debug_frame.shape[0] - fixed_bottom_height + 30)
        put_centered_text(debug_frame, "Variable Area", (fixed_top_height + debug_frame.shape[0] - fixed_bottom_height) // 2)
        put_centered_text(debug_frame, "Content End", content_end + 30)
        if overlap_region:
            put_centered_text(debug_frame, "Overlap Area", overlap_region[0] + 30)
        if new_content_start:
            put_centered_text(debug_frame, "New Content Start", new_content_start - 30)
        
        # 在图片中央添加状态文字
        put_centered_text(debug_frame, status, debug_frame.shape[0] // 2)
        
        filename = f"{self.debug_output_dir}/frame_{frame_number:04d}_{status}.jpg"
        cv2.imwrite(filename, debug_frame)
        self.log(f"Saved debug frame: {filename}")

    def crop_frame(self, frame, start_y):
        return frame[start_y:, :]

    def find_non_empty_content_end(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
        non_zero_rows = np.where(np.sum(binary, axis=1) > frame.shape[1] * 0.05)[0]  # 忽略几乎为空的行
        return non_zero_rows[-1] if len(non_zero_rows) > 0 else 0
