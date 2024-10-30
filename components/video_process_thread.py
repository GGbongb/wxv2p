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
        os.makedirs(self.debug_output_dir, exist_ok=True)
        
        # 调整参数
        self.fixed_top_height = 120
        self.fixed_bottom_height = 70
        self.reference_frame = None  # 存储参考帧
        self.movement_threshold = 400  # 移动距离阈值，超过这个值就提取新的参考帧

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

    def create_tracking_visualization(self, curr_frame, accumulated_movement):
        """创建参考帧和当前帧的对比可视化"""
        try:
            if self.reference_frame is None:
                self.reference_frame = curr_frame.copy()
                return None
            
            # 创建可视化图像
            vis_image = np.hstack((self.reference_frame, curr_frame))
            
            # 获取可变区域
            content_start = self.fixed_top_height
            content_end = curr_frame.shape[0] - self.fixed_bottom_height
            
            # 在当前帧中画垂直线表示累积移动距离
            start_y = curr_frame.shape[0] - self.fixed_bottom_height
            end_y = start_y - accumulated_movement
            mid_x = curr_frame.shape[1] // 2 + self.reference_frame.shape[1]  # 在右图中间
            
            # 画移动距离线
            cv2.line(vis_image, 
                    (mid_x, int(start_y)), 
                    (mid_x, int(end_y)), 
                    (0, 255, 0), 2)  # 绿色线
            
            # 添加移动距离信息
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(vis_image, 
                       f"Movement: {accumulated_movement:.1f}px", 
                       (mid_x - 100, 30), font, 0.7, (0, 255, 0), 2)
            
            # 添加阈值线
            threshold_y = start_y - self.movement_threshold
            cv2.line(vis_image,
                    (self.reference_frame.shape[1], int(threshold_y)),
                    (vis_image.shape[1], int(threshold_y)),
                    (0, 0, 255), 1)  # 红色阈值线
            
            # 画出固定区域的边界线
            for x in [0, self.reference_frame.shape[1]]:
                cv2.line(vis_image, 
                        (x, content_start), 
                        (x + self.reference_frame.shape[1], content_start), 
                        (255, 255, 0), 1)  # 黄色线
                cv2.line(vis_image, 
                        (x, content_end), 
                        (x + self.reference_frame.shape[1], content_end), 
                        (255, 255, 0), 1)  # 黄色线
            
            return vis_image

        except Exception as e:
            self.log(f"Error in create_tracking_visualization: {str(e)}")
            import traceback
            self.log(traceback.format_exc())
            return None

    def calculate_movement(self, prev_frame, curr_frame):
        """计算两帧之间的移动距离"""
        try:
            # 转换为灰度图
            prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
            curr_gray = cv2.cvtColor(curr_frame, cv2.COLOR_BGR2GRAY)
            
            # 获取可变区域
            content_start = self.fixed_top_height
            content_end = curr_frame.shape[0] - self.fixed_bottom_height
            
            # 在可变区域内检测特征点
            prev_content = prev_gray[content_start:content_end, :]
            
            # 使用Shi-Tomasi角点检测
            features = cv2.goodFeaturesToTrack(
                prev_content,
                maxCorners=100,
                qualityLevel=0.3,
                minDistance=7,
                blockSize=7
            )
            
            if features is None:
                return 0
                
            # 调整特征点坐标以匹配完整图像
            features = np.array([[[pt[0][0], pt[0][1] + content_start]] for pt in features], dtype=np.float32)
            
            # 使用光流法追踪特征点
            next_features, status, error = cv2.calcOpticalFlowPyrLK(
                prev_gray, curr_gray, features, None
            )
            
            # 计算有效的位移
            displacements = []
            for i, (new, old) in enumerate(zip(next_features, features)):
                if status[i]:
                    displacement = new[0][1] - old[0][1]  # 只关注y方向的位移
                    displacements.append(displacement)
            
            if displacements:
                return abs(np.mean(displacements))  # 返回平均位移的绝对值
            return 0

        except Exception as e:
            self.log(f"Error in calculate_movement: {str(e)}")
            return 0

    def run(self):
        try:
            cap = cv2.VideoCapture(self.video_path)
            if not cap.isOpened():
                raise Exception("Error opening video file")

            total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            prev_frame = None
            frame_count = 0
            accumulated_movement = 0  # 累积移动距离

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                if prev_frame is not None:
                    # 计算移动距离
                    movement = self.calculate_movement(prev_frame, frame)
                    accumulated_movement += movement
                    
                    # 创建可视化图像
                    vis_image = self.create_tracking_visualization(frame, accumulated_movement)
                    if vis_image is not None:
                        cv2.imwrite(f"{self.debug_output_dir}/tracking_{frame_count:04d}.jpg", vis_image)
                    
                    # 检查是否需要更新参考帧
                    if accumulated_movement >= self.movement_threshold:
                        self.reference_frame = frame.copy()
                        accumulated_movement = 0
                        self.log(f"New reference frame captured at frame {frame_count}")

                prev_frame = frame.copy()
                frame_count += 1
                
                # 发送进度信号
                progress = int((frame_count / total_frames) * 100)
                self.progress.emit(progress)

            cap.release()
            self.finished.emit([])

        except Exception as e:
            self.log(f"Error in run: {str(e)}")
            import traceback
            self.log(traceback.format_exc())