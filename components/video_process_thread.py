import cv2
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal
import logging
import os
import logging
logger = logging.getLogger(__name__)
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
        
        # 移除固定区域的限制
        self.reference_frame = None
        self.movement_threshold = 600  # 移动阈值
        
        # 特征点追踪参数
        self.max_corners = 200  # 增加特征点数量
        self.quality_level = 0.3
        self.min_distance = 7
        self.block_size = 7

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
    
    def calculate_speed(self, movement, fps=30):
        """计算页面滑动速度（像素/秒）"""
        return abs(movement * fps)



    def calculate_movement(self, prev_frame, curr_frame):
        """计算两帧之间的移动距离，增加鲁棒性"""
        try:
            # 转换为灰度图
            prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
            curr_gray = cv2.cvtColor(curr_frame, cv2.COLOR_BGR2GRAY)
            
            # 检测特征点
            features = cv2.goodFeaturesToTrack(
                prev_gray,
                maxCorners=self.max_corners,
                qualityLevel=self.quality_level,
                minDistance=self.min_distance,
                blockSize=self.block_size
            )
            
            if features is None or len(features) < 10:  # 确保有足够的特征点
                return 0
                
            # 使用光流法追踪特征点
            next_features, status, error = cv2.calcOpticalFlowPyrLK(
                prev_gray, curr_gray, features, None
            )
            
            # 计算有效的位移
            displacements = []
            for i, (new, old) in enumerate(zip(next_features, features)):
                if status[i]:
                    displacement = new[0][1] - old[0][1]  # 垂直方向位移
                    displacements.append(displacement)
            
            if not displacements:
                return 0
                
            # 使用中位数来降低异常值影响
            median_displacement = np.median(displacements)
            
            # 过滤掉偏离中位数过大的位移
            filtered_displacements = [d for d in displacements 
                                    if abs(d - median_displacement) < 20]  # 20px 阈值
            
            if filtered_displacements:
                return abs(np.mean(filtered_displacements))
            return 0

        except Exception as e:
            self.log(f"Error in calculate_movement: {str(e)}")
            return 0

    def run(self):
        try:
            logger.debug(f"处理视频: {self.video_path}")
            # 这里是处理视频的逻辑
            # 例如，读取视频帧并发送进度信号
            cap = cv2.VideoCapture(self.video_path)
            if not cap.isOpened():
                raise Exception("Error opening video file")

            total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            prev_frame = None
            frame_count = 0
            accumulated_movement = 0
            extracted_frames = []
            last_movement = 0
            movement_direction_changes = 0

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                # 保存第一帧
                if prev_frame is None:
                    self.reference_frame = frame.copy()
                    extracted_frames.append(frame.copy())  # 添加这行，保存第一帧
                    self.log("First frame captured")
                else:
                    # 其余代码保持不变
                    movement = self.calculate_movement(prev_frame, frame)
                    
                    if last_movement * movement < 0:
                        movement_direction_changes += 1
                    last_movement = movement
                    
                    if movement_direction_changes > 3:
                        movement = 0
                        movement_direction_changes = 0
                    
                    accumulated_movement += movement
                    
                    vis_image = self.create_tracking_visualization(frame, accumulated_movement)
                    if vis_image is not None:
                        cv2.imwrite(f"{self.debug_output_dir}/tracking_{frame_count:04d}.jpg", vis_image)
                    
                    if accumulated_movement >= self.movement_threshold:
                        self.reference_frame = frame.copy()
                        accumulated_movement = 0
                        movement_direction_changes = 0
                        self.log(f"New reference frame captured at frame {frame_count}")
                        extracted_frames.append(frame.copy())

                prev_frame = frame.copy()
                frame_count += 1
                
                progress = int((frame_count / total_frames) * 100)
                self.progress.emit(progress)

            cap.release()
            self.finished.emit(extracted_frames)
            logger.debug("视频处理完成")

        except Exception as e:
            self.log(f"Error in run: {str(e)}")
            import traceback
            self.log(traceback.format_exc())
