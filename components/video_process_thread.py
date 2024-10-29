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

    def get_content_regions(self, frame):
        """获取多个检测区域"""
        height = frame.shape[0]
        content_start = self.fixed_top_height
        content_end = height - self.fixed_bottom_height
        
        # 将内容区域分成多个子区域
        region_height = (content_end - content_start) // 3
        
        top_region = frame[content_start:content_start + region_height]
        mid_region = frame[content_start + region_height:content_start + 2*region_height]
        bottom_region = frame[content_start + 2*region_height:content_end]
        
        return top_region, mid_region, bottom_region

    def compute_similarity_with_sliding_window(self, ref_region, curr_frame, max_offset=50):
        """使用滑动窗口计算最佳匹配位置和相似度"""
        try:
            height = curr_frame.shape[0]
            ref_height = ref_region.shape[0]
            best_similarity = 0
            best_position = 0
            
            # 在当前帧中上下滑动搜索参考区域
            for offset in range(-max_offset, max_offset + 1):
                start_y = max(0, self.fixed_top_height + offset)
                end_y = min(height - self.fixed_bottom_height, start_y + ref_height)
                
                if end_y - start_y < ref_height * 0.5:  # 确保有足够的重叠区域
                    continue
                    
                curr_region = curr_frame[start_y:end_y]
                if curr_region.shape[0] != ref_region.shape[0]:
                    curr_region = cv2.resize(curr_region, (ref_region.shape[1], ref_region.shape[0]))
                
                similarity = self.compute_similarity(ref_region, curr_region)
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_position = start_y
            
            return best_similarity, best_position
        
        except Exception as e:
            self.log(f"Error in compute_similarity_with_sliding_window: {str(e)}")
            import traceback
            self.log(traceback.format_exc())
            raise

    def compute_overlap_ratio(self, ref_region, curr_region):
        """计算参考区域与当前区域的重叠比例"""
        # 确保两个区域大小相同
        if ref_region.shape != curr_region.shape:
            curr_region = cv2.resize(curr_region, (ref_region.shape[1], ref_region.shape[0]))
        
        # 转换为灰度图
        if len(ref_region.shape) == 3:
            ref_region = cv2.cvtColor(ref_region, cv2.COLOR_BGR2GRAY)
        if len(curr_region.shape) == 3:
            curr_region = cv2.cvtColor(curr_region, cv2.COLOR_BGR2GRAY)
        
        # 计算重叠区域
        overlap = cv2.bitwise_and(ref_region, curr_region)
        overlap_area = np.sum(overlap > 0)
        ref_area = np.sum(ref_region > 0)
        
        # 计算重叠比例
        overlap_ratio = overlap_area / ref_area if ref_area > 0 else 0
        return overlap_ratio

    def create_comparison_visualization(self, reference_regions, current_frame, overlap_ratios, positions):
        """创建带有详细标注的对比图像"""
        try:
            ref_top, ref_mid, ref_bottom = reference_regions
            height = current_frame.shape[0]
            width = current_frame.shape[1]
            
            # 创建参考区域的组合图像
            ref_combined = np.vstack(reference_regions)
            
            # 调整参考区域组合图像的大小，使其高度与当前帧匹配
            ref_combined = cv2.resize(ref_combined, (width, height))
            
            # 在当前帧中标记重叠比例和匹配位置
            marked_frame = current_frame.copy()
            for i, (ratio, pos) in enumerate(zip(overlap_ratios, positions)):
                ref_height = reference_regions[i].shape[0]
                # 绘制参考区域的框
                cv2.rectangle(ref_combined, 
                             (0, i * ref_height), 
                             (width, (i + 1) * ref_height),
                             (255, 0, 0), 2)  # 蓝色框表示参考区域
                
                # 绘制匹配区域的框
                cv2.rectangle(marked_frame, 
                             (0, pos), 
                             (width, pos + ref_height),
                             (0, 255, 0), 2)  # 绿色框表示匹配区域
                
                # 添加重叠比例标注
                cv2.putText(marked_frame, 
                           f"Overlap: {ratio:.2f}", 
                           (10, pos + 20), 
                           cv2.FONT_HERSHEY_SIMPLEX, 
                           0.6, (0, 0, 255), 2)
            
            # 将参考区域和标记后的当前帧并排显示
            comparison_image = np.hstack((ref_combined, marked_frame))
            
            # 添加标题和说明
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(comparison_image, "Reference Regions", 
                       (10, 30), font, 1, (0, 255, 0), 2)
            cv2.putText(comparison_image, "Current Frame (with overlap)", 
                       (width + 10, 30), font, 1, (0, 255, 0), 2)
            
            return comparison_image

        except Exception as e:
            self.log(f"Error in create_comparison_visualization: {str(e)}")
            import traceback
            self.log(traceback.format_exc())
            raise

    def check_content_changed(self, reference_regions, current_frame):
        """检查参考内容是否真正消失"""
        try:
            ref_top, ref_mid, ref_bottom = reference_regions
            
            # 对每个参考区域在当前帧中进行滑动窗口匹配
            overlap_ratios = []
            positions = []
            for ref_region in [ref_top, ref_mid, ref_bottom]:
                best_overlap_ratio = 0
                best_position = 0
                for offset in range(-50, 51):  # 滑动窗口范围
                    start_y = max(0, self.fixed_top_height + offset)
                    end_y = min(current_frame.shape[0] - self.fixed_bottom_height, start_y + ref_region.shape[0])
                    
                    if end_y - start_y < ref_region.shape[0] * 0.5:
                        continue
                    
                    curr_region = current_frame[start_y:end_y]
                    overlap_ratio = self.compute_overlap_ratio(ref_region, curr_region)
                    
                    if overlap_ratio > best_overlap_ratio:
                        best_overlap_ratio = overlap_ratio
                        best_position = start_y
                
                overlap_ratios.append(best_overlap_ratio)
                positions.append(best_position)
            
            # 记录详细的重叠比例信息
            self.log(f"Overlap ratios: {overlap_ratios}")
            
            # 创建带标注的对比图像
            comparison_image = self.create_comparison_visualization(
                reference_regions, current_frame, overlap_ratios, positions)
            
            # 判断内容是否真正消失（所有区域的重叠比例都很低）
            content_changed = all(ratio < 0.2 for ratio in overlap_ratios)  # 设定重叠比例阈值
            max_overlap_ratio = max(overlap_ratios)
            
            return content_changed, max_overlap_ratio, comparison_image

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
            reference_regions = None
            skip_count = 0

            for i in range(total_frames):
                try:
                    ret, frame = cap.read()
                    if not ret:
                        break

                    if len(frames) == 0:
                        frames.append(frame)
                        reference_regions = self.get_content_regions(frame)
                        self.save_debug_frame(frame, i, "First")
                        continue

                    # 每隔几帧检查一次
                    skip_count += 1
                    if skip_count < 3:
                        continue
                    skip_count = 0

                    # 直接传入当前帧，而不是regions
                    changed, similarity, comparison_image = self.check_content_changed(
                        reference_regions, frame)  # 修改这里
                    
                    status = f"Similarity_{similarity:.4f}"
                    self.save_comparison_image(comparison_image, i, status)
                    
                    if changed:
                        frames.append(frame)
                        reference_regions = self.get_content_regions(frame)
                        self.log(f"Content completely changed, captured frame {len(frames)}")
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

