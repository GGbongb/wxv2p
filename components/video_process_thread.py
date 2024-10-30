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

    def create_tracking_visualization(self, prev_frame, curr_frame):
        """创建特征点追踪的可视化效果"""
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
                self.log("No features found in the previous frame")
                return None
                
            # 调整特征点坐标以匹配完整图像
            features = np.array([[[pt[0][0], pt[0][1] + content_start]] for pt in features], dtype=np.float32)
            
            # 使用光流法追踪特征点
            next_features, status, error = cv2.calcOpticalFlowPyrLK(
                prev_gray, curr_gray, features, None
            )
            
            # 创建可视化图像
            vis_image = np.hstack((prev_frame, curr_frame))
            
            # 计算特征点的位移
            displacements = []
            
            # 计算有效的位移
            for i, (new, old) in enumerate(zip(next_features, features)):
                if status[i]:
                    displacement = new[0][1] - old[0][1]  # 只关注y方向的位移
                    displacements.append(displacement)
            
            if displacements:
                # 计算平均位移
                mean_displacement = np.mean(displacements)
                
                # 在两个图像中画垂直线表示移动
                # 左图：从底部到顶部的红线
                start_y = curr_frame.shape[0] - self.fixed_bottom_height
                end_y = start_y - abs(mean_displacement)
                mid_x = prev_frame.shape[1] // 2
                
                # 在左图画线
                cv2.line(vis_image, 
                        (mid_x, int(start_y)), 
                        (mid_x, int(end_y)), 
                        (0, 0, 255), 2)  # 红色线
                
                # 在右图画线
                cv2.line(vis_image, 
                        (mid_x + prev_frame.shape[1], int(start_y)), 
                        (mid_x + prev_frame.shape[1], int(end_y)), 
                        (0, 255, 0), 2)  # 绿色线
                
                # 添加位移信息
                font = cv2.FONT_HERSHEY_SIMPLEX
                cv2.putText(vis_image, 
                           f"Displacement: {abs(mean_displacement):.1f}px", 
                           (10, 30), font, 0.7, (0, 255, 0), 2)
                
                # 画出固定区域的边界线
                cv2.line(vis_image, 
                        (0, content_start), 
                        (vis_image.shape[1], content_start), 
                        (255, 255, 0), 1)  # 黄色线
                cv2.line(vis_image, 
                        (0, content_end), 
                        (vis_image.shape[1], content_end), 
                        (255, 255, 0), 1)  # 黄色线
            
            return vis_image

        except Exception as e:
            self.log(f"Error in create_tracking_visualization: {str(e)}")
            import traceback
            self.log(traceback.format_exc())
            return None

    def run(self):
        try:
            cap = cv2.VideoCapture(self.video_path)
            if not cap.isOpened():
                raise Exception("Error opening video file")

            total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            prev_frame = None
            frame_count = 0

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                if prev_frame is not None:
                    # 创建追踪可视化
                    vis_image = self.create_tracking_visualization(prev_frame, frame)
                    if vis_image is not None:
                        # 保存可视化结果
                        cv2.imwrite(f"{self.debug_output_dir}/tracking_{frame_count:04d}.jpg", vis_image)

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