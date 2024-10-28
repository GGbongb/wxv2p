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
        self.check_height = 180  # 检查区域的总高度
        self.similarity_threshold = 0.7  # 相似度阈值

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

    def get_check_region(self, frame, is_bottom=False):
        """获取检查区域"""
        if is_bottom:
            return frame[-self.fixed_bottom_height-self.check_height:-self.fixed_bottom_height]
        else:
            return frame[self.fixed_top_height:self.fixed_top_height+self.check_height]

    def check_similarity(self, last_regions, current_regions):
        try:
            last_region = last_regions[0]  # 只需要完整区域
            current_region = current_regions[0]
            
            # 保存引用供显示使用
            self.last_region = last_region
            self.current_region = current_region
            
            # 计算区域相似度
            similarity = self.compute_similarity(last_region, current_region)
            
            # 创建对比图像
            comparison_image = np.hstack((last_region, current_region))
            
            return similarity, similarity, comparison_image

        except Exception as e:
            self.log(f"Error in check_similarity: {str(e)}")
            import traceback
            self.log(traceback.format_exc())
            raise

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
        
        # 应用高斯模糊减少噪声
        img1 = cv2.GaussianBlur(img1, (3, 3), 0)
        img2 = cv2.GaussianBlur(img2, (3, 3), 0)
        
        # 模板匹配
        result = cv2.matchTemplate(img1, img2, cv2.TM_CCOEFF_NORMED)
        template_sim = np.max(result)
        
        # 直方图比较
        hist1 = cv2.calcHist([img1], [0], None, [256], [0, 256])
        hist2 = cv2.calcHist([img2], [0], None, [256], [0, 256])
        hist_sim = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
        
        return (template_sim + hist_sim) / 2

    def run(self):
        try:
            cap = cv2.VideoCapture(self.video_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.log(f"Total frames: {total_frames}")

            frames = []
            last_regions = None

            for i in range(total_frames):
                try:
                    ret, frame = cap.read()
                    if not ret:
                        self.log(f"Failed to read frame {i}")
                        break

                    if len(frames) == 0:
                        frames.append(frame)
                        last_regions = (self.get_check_region(frame, True), None, None)
                        self.log("First frame processed successfully")
                        self.save_debug_frame(frame, i, "First")
                        continue

                    self.log(f"Processing frame {i}")
                    current_regions = (self.get_check_region(frame), None, None)
                    similarity, _, comparison_image = self.check_similarity(last_regions, current_regions)
                    
                    status = f"Similarity_{similarity:.4f}"
                    self.save_comparison_image(comparison_image, i, status)
                    
                    if similarity >= self.similarity_threshold:
                        frames.append(frame)
                        last_regions = (self.get_check_region(frame, True), None, None)
                        self.log(f"Added new frame {len(frames)}, similarity: {similarity:.4f}")
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
        debug_frame = frame.copy()
        
        # 绘制固定区域的线和检查区域
        cv2.line(debug_frame, (0, self.fixed_top_height), 
                 (debug_frame.shape[1], self.fixed_top_height), (0, 255, 0), 2)
        cv2.line(debug_frame, (0, debug_frame.shape[0] - self.fixed_bottom_height), 
                 (debug_frame.shape[1], debug_frame.shape[0] - self.fixed_bottom_height), (0, 255, 0), 2)
        
        # 绘制检查区域（红色）
        cv2.rectangle(debug_frame, 
                    (0, self.fixed_top_height), 
                    (debug_frame.shape[1], self.fixed_top_height + self.check_height), 
                    (0, 0, 255), 2)
        cv2.rectangle(debug_frame, 
                    (0, debug_frame.shape[0] - self.fixed_bottom_height - self.check_height), 
                    (debug_frame.shape[1], debug_frame.shape[0] - self.fixed_bottom_height), 
                    (0, 0, 255), 2)
        
        # 添加标注文字
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(debug_frame, "Check Region", (10, self.fixed_top_height - 10), 
                    font, 0.7, (0, 0, 255), 2)
        cv2.putText(debug_frame, status, (10, 30), font, 1, (0, 0, 255), 2)
        
        filename = f"{self.debug_output_dir}/frame_{frame_number:04d}_{status}.jpg"
        cv2.imwrite(filename, debug_frame)
        self.log(f"Saved debug frame: {filename}")

    def save_comparison_image(self, comparison_image, frame_number, status):
        try:
            extended_height = self.check_height
            width = comparison_image.shape[1]
            
            # 创建白色背景
            full_comparison = np.ones((extended_height + 50, width, 3), dtype=np.uint8) * 255
            
            # 复制检查区域图像
            if hasattr(self, 'last_region') and hasattr(self, 'current_region'):
                full_comparison[0:extended_height, :width] = self.last_region
                full_comparison[0:extended_height, width:] = self.current_region
                
                # 在检查区域上标记实际重复区域（蓝色矩形）
                if hasattr(self, 'last_region') and hasattr(self, 'current_region'):
                    # 标记 Last Repeat 中的重复区域
                    cv2.rectangle(full_comparison, 
                                (0, extended_height - self.check_height), 
                                (width, extended_height), 
                                (255, 0, 0), 2)
                    
                    # 标记 Current Top 中的重复区域
                    cv2.rectangle(full_comparison, 
                                (0, 0), 
                                (width, self.check_height), 
                                (255, 0, 0), 2)
            
            # 添加标注
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(full_comparison, "Last Repeat", (10, 30), font, 1, (0, 255, 0), 2)
            cv2.putText(full_comparison, "Current Top", (10, 30), font, 1, (0, 255, 0), 2)
            cv2.putText(full_comparison, "Matched Region", (10, extended_height - 5), font, 0.7, (255, 0, 0), 2)
            cv2.putText(full_comparison, status, (10, extended_height + 30), font, 0.7, (0, 0, 255), 2)
            
            filename = f"{self.repeat_region_dir}/comparison_{frame_number:04d}_{status}.jpg"
            cv2.imwrite(filename, full_comparison)
            self.log(f"Saved comparison image: {filename}")
            
        except Exception as e:
            self.log(f"Error in save_comparison_image: {str(e)}")
            import traceback
            self.log(traceback.format_exc())
