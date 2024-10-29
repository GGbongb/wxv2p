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
        
        # 调整参数
        self.fixed_top_height = 120
        self.fixed_bottom_height = 70
        self.content_height = 400  # 增加内容检测区域高度，确保能包含主要内容
        self.similarity_threshold = 0.6  # 相似度阈值
        self.ignore_edge_pixels = 20  # 忽略边缘像素

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

    def compute_similarity(self, img1, img2):
        """计算两个图像的相似度"""
        if img1 is None or img2 is None:
            raise ValueError("One of the input images is None")
        
        # 确保两个图像大小相同
        if img1.shape != img2.shape:
            self.log(f"Image shapes don't match: {img1.shape} vs {img2.shape}")
            img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))
        
        # 转换为灰度图
        if len(img1.shape) == 3:
            img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        if len(img2.shape) == 3:
            img2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
        
        # 忽略边缘区域
        img1 = img1[:, self.ignore_edge_pixels:-self.ignore_edge_pixels]
        img2 = img2[:, self.ignore_edge_pixels:-self.ignore_edge_pixels]
        
        # 应用高斯模糊减少噪声
        img1 = cv2.GaussianBlur(img1, (3, 3), 0)
        img2 = cv2.GaussianBlur(img2, (3, 3), 0)
        
        # 应用自适应阈值
        img1_thresh = cv2.adaptiveThreshold(img1, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                        cv2.THRESH_BINARY, 11, 2)
        img2_thresh = cv2.adaptiveThreshold(img2, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                        cv2.THRESH_BINARY, 11, 2)
        
        # 计算相似度
        result = cv2.matchTemplate(img1_thresh, img2_thresh, cv2.TM_CCOEFF_NORMED)
        similarity = np.max(result)
        
        return similarity

    def get_content_region(self, frame):
        """获取内容区域（中间的主要内容区）"""
        height = frame.shape[0]
        # 提取固定区域之间的内容区域
        content_region = frame[self.fixed_top_height:height - self.fixed_bottom_height]
        return content_region

    def check_content_changed(self, reference_content, current_content):
        """检查参考内容是否已经完全消失"""
        try:
            # 计算相似度
            similarity = self.compute_similarity(reference_content, current_content)
            
            # 如果相似度很低，说明参考内容已经完全消失
            content_changed = similarity < self.similarity_threshold
            
            # 创建对比图像
            comparison_image = np.hstack((reference_content, current_content))
            
            return content_changed, similarity, comparison_image

        except Exception as e:
            self.log(f"Error in check_content_changed: {str(e)}")
            import traceback
            self.log(traceback.format_exc())
            raise

    def run(self):
        try:
            cap = cv2.VideoCapture(self.video_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.log(f"Total frames: {total_frames}")

            frames = []
            reference_content = None
            skip_count = 0

            for i in range(total_frames):
                try:
                    ret, frame = cap.read()
                    if not ret:
                        break

                    if len(frames) == 0:
                        frames.append(frame)
                        reference_content = self.get_content_region(frame)
                        self.save_debug_frame(frame, i, "First")
                        continue

                    # 每隔几帧检查一次
                    skip_count += 1
                    if skip_count < 3:
                        continue
                    skip_count = 0

                    current_content = self.get_content_region(frame)
                    changed, similarity, comparison_image = self.check_content_changed(
                        reference_content, current_content)
                    
                    status = f"Similarity_{similarity:.4f}"
                    self.save_comparison_image(comparison_image, i, status)
                    
                    if changed:
                        frames.append(frame)
                        reference_content = self.get_content_region(frame)
                        self.log(f"Content changed, captured frame {len(frames)}")
                        self.save_debug_frame(frame, i, f"Frame_{len(frames)}")
                    else:
                        self.save_debug_frame(frame, i, f"Skipped_{status}")

                    self.progress.emit(int((i + 1) / total_frames * 100))

                except Exception as e:
                    self.log(f"Error processing frame {i}: {str(e)}")
                    import traceback
                    self.log(traceback.format_exc())
                    break
                if i > 400:
                    break

            cap.release()
            self.log(f"Processing completed. Total frames captured: {len(frames)}")
            self.finished.emit(frames)

        except Exception as e:
            self.log(f"Critical error in run method: {str(e)}")
            import traceback
            self.log(traceback.format_exc())
            self.finished.emit([])

    def save_debug_frame(self, frame, frame_number, status):
        """保存调试帧"""
        debug_frame = frame.copy()
        height = frame.shape[0]
        
        # 绘制检测区域
        cv2.rectangle(debug_frame, 
                    (0, self.fixed_top_height), 
                    (frame.shape[1], self.fixed_top_height + self.content_height), 
                    (0, 255, 0), 2)
        
        cv2.rectangle(debug_frame, 
                    (0, height//2 - self.content_height//2), 
                    (frame.shape[1], height//2 + self.content_height//2), 
                    (0, 255, 0), 2)
        
        cv2.rectangle(debug_frame, 
                    (0, height - self.fixed_bottom_height - self.content_height), 
                    (frame.shape[1], height - self.fixed_bottom_height), 
                    (0, 255, 0), 2)
        
        # 添加标注
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(debug_frame, "Content Regions", (10, 30), font, 1, (0, 255, 0), 2)
        cv2.putText(debug_frame, status, (10, 60), font, 1, (0, 0, 255), 2)
        
        filename = f"{self.debug_output_dir}/frame_{frame_number:04d}_{status}.jpg"
        cv2.imwrite(filename, debug_frame)
        self.log(f"Saved debug frame: {filename}")

    def save_comparison_image(self, comparison_image, frame_number, status):
        """保存对比图像"""
        try:
            # 添加标注
            font = cv2.FONT_HERSHEY_SIMPLEX
            height = comparison_image.shape[0]
            width = comparison_image.shape[1]
            
            # 在图像上添加标注
            cv2.putText(comparison_image, "First Frame", (10, 30), font, 1, (0, 255, 0), 2)
            cv2.putText(comparison_image, "Current Frame", (width//2 + 10, 30), font, 1, (0, 255, 0), 2)
            cv2.putText(comparison_image, status, (10, height - 10), font, 0.7, (0, 0, 255), 2)
            
            filename = f"{self.repeat_region_dir}/comparison_{frame_number:04d}_{status}.jpg"
            cv2.imwrite(filename, comparison_image)
            self.log(f"Saved comparison image: {filename}")
            
        except Exception as e:
            self.log(f"Error in save_comparison_image: {str(e)}")
            import traceback
            self.log(traceback.format_exc())

