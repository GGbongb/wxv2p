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
        self.repeat_check_height = 90  # 区域1的高度
        self.region2_height = 90       # 区域2的高度
        # 扩展区域的总高度是区域1和区域2的高度之和
        self.extended_check_height = self.repeat_check_height + self.region2_height
        self.rough_similarity_threshold = 0.65  # 扩展区域的相似度阈值（降低阈值）
        self.fine_similarity_threshold = 0.70   # 区域1的相似度阈值（降低阈值）

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
                        last_regions = self.get_repeat_region(frame)
                        self.log("Processing first frame")
                        self.save_debug_frame(frame, i, "First", self.fixed_top_height, self.fixed_bottom_height)
                        self.save_repeat_region(last_regions[1], i, "First_Repeat")
                        self.log("First frame processed successfully")
                        continue

                    self.log(f"Processing frame {i}")
                    current_regions = self.get_top_region(frame)
                    full_sim, region1_sim, comparison_image = self.check_similarity(last_regions, current_regions)
                    
                    status = f"Full_{full_sim:.4f}_Region1_{region1_sim:.4f}"
                    self.save_comparison_image(comparison_image, i, status)
                    
                    if full_sim >= self.rough_similarity_threshold and region1_sim >= self.fine_similarity_threshold:
                        frames.append(frame)
                        last_regions = self.get_repeat_region(frame)
                        self.log(f"Added new frame {len(frames)}, similarities: {status}")
                        self.save_debug_frame(frame, i, f"Frame_{len(frames)}", self.fixed_top_height, self.fixed_bottom_height)
                        self.save_repeat_region(last_regions[1], i, f"NewRepeat_{len(frames)}")
                    else:
                        self.save_debug_frame(frame, i, f"Skipped_{status}", self.fixed_top_height, self.fixed_bottom_height)

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
            self.finished.emit([])  # 发送空列表表示处理失败

    def get_repeat_region(self, frame):
        total_height = self.repeat_check_height + self.region2_height
        region = frame[-self.fixed_bottom_height-total_height:-self.fixed_bottom_height]
        region1 = region[-self.repeat_check_height:]  # 下面的区域1
        region2 = region[:-self.repeat_check_height]  # 上面的区域2
        return region, region1, region2

    def get_top_region(self, frame):
        total_height = self.repeat_check_height + self.region2_height
        region = frame[self.fixed_top_height:self.fixed_top_height+total_height]
        region1 = region[:self.repeat_check_height]   # 上面的区域1
        region2 = region[self.repeat_check_height:]   # 下面的区域2
        return region, region1, region2

    def check_similarity(self, last_regions, current_regions):
        try:
            last_full, last_region1, last_region2 = last_regions
            current_full, current_region1, current_region2 = current_regions
            
            # 保存引用供显示使用
            self.last_extended_repeat = last_full      # 添加这行
            self.current_extended_top = current_full   # 添加这行
            self.last_region1 = last_region1
            self.current_region1 = current_region1
        
            
            # 转换为灰度图像并进行边缘模糊处理
            def preprocess_image(img):
                if img is None:
                    raise ValueError("Input image is None")
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                blur = cv2.GaussianBlur(gray, (3, 3), 0)
                return blur
            
            # 计算相似度（使用多个方法）
            def compute_similarity(img1, img2):
                if img1 is None or img2 is None:
                    raise ValueError("One of the input images is None")
                # 确保两个图像大小相同
                if img1.shape != img2.shape:
                    self.log(f"Image shapes don't match: {img1.shape} vs {img2.shape}")
                    img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))
                
                # 模板匹配
                result = cv2.matchTemplate(img1, img2, cv2.TM_CCOEFF_NORMED)
                template_sim = np.max(result)
                
                # 直方图比较
                hist1 = cv2.calcHist([img1], [0], None, [256], [0, 256])
                hist2 = cv2.calcHist([img2], [0], None, [256], [0, 256])
                hist_sim = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
                
                return (template_sim + hist_sim) / 2
            
            # 记录图像尺寸
            self.log(f"Last full region shape: {last_full.shape}")
            self.log(f"Current full region shape: {current_full.shape}")
            
            # 计算扩展区域的相似度
            full_sim = compute_similarity(
                preprocess_image(last_full),
                preprocess_image(current_full)
            )
            
            # 如果扩展区域相似度达到阈值，再计算区域1的相似度
            if full_sim >= self.rough_similarity_threshold:
                region1_sim = compute_similarity(
                    preprocess_image(last_region1),
                    preprocess_image(current_region1)
                )
            else:
                region1_sim = 0
            
            comparison_image = np.hstack((last_region1, current_region1))
            return full_sim, region1_sim, comparison_image

        except Exception as e:
            self.log(f"Error in check_similarity: {str(e)}")
            import traceback
            self.log(traceback.format_exc())
            raise
    
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
        
        try:
            # 复制扩展区域图像
            if hasattr(self, 'last_extended_repeat') and hasattr(self, 'current_extended_top'):
                full_comparison[0:extended_height, :width//2] = self.last_extended_repeat
                full_comparison[0:extended_height, width//2:] = self.current_extended_top
            else:
                self.log("Warning: Extended regions not available")
                # 如果没有扩展区域，就只显示实际区域
                full_comparison[0:actual_height, :width//2] = comparison_image[:, :width//2]
                full_comparison[0:actual_height, width//2:] = comparison_image[:, width//2:]
            
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
            
        except Exception as e:
            self.log(f"Error in save_comparison_image: {str(e)}")
            import traceback
            self.log(traceback.format_exc())

