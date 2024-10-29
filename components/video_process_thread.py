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

    def create_comparison_visualization(self, reference_regions, current_frame, disappearance_ratios):
        """创建带有详细标注的对比图像"""
        try:
            ref_top, ref_mid, ref_bottom = reference_regions
            height = current_frame.shape[0]
            width = current_frame.shape[1]
            
            # 裁剪当前帧，去掉顶部和底部固定区域
            content_start = self.fixed_top_height
            content_end = height - self.fixed_bottom_height
            current_content = current_frame[content_start:content_end].copy()
            
            # 创建参考区域的组合图像
            ref_combined = np.vstack(reference_regions)
            
            # 调整参考区域组合图像的大小，使其高度与当前内容区域匹配
            ref_combined = cv2.resize(ref_combined, (width, content_end - content_start))
            
            # 在当前内容区域中标记消失度
            marked_content = current_content.copy()
            for i, ratio in enumerate(disappearance_ratios):
                ref_height = reference_regions[i].shape[0]
                y_pos = i * (current_content.shape[0] // 3)  # 平均分配高度
                
                # 绘制参考区域的框
                cv2.rectangle(ref_combined, 
                             (0, i * ref_height), 
                             (width, (i + 1) * ref_height),
                             (255, 0, 0), 2)  # 蓝色框表示参考区域
                
                # 绘制当前区域的框，颜色根据消失度变化
                color = (
                    0,  # B
                    int(255 * (1 - ratio)),  # G（消失度越高越少绿色）
                    int(255 * ratio)  # R（消失度越高越多红色）
                )
                cv2.rectangle(marked_content, 
                             (0, y_pos), 
                             (width, y_pos + ref_height),
                             color, 2)
                
                # 添加消失度标注
                cv2.putText(marked_content, 
                           f"Disappeared: {ratio:.2f}", 
                           (10, y_pos + 20), 
                           cv2.FONT_HERSHEY_SIMPLEX, 
                           0.6, (0, 0, 255), 2)
            
            # 将参考区域和标记后的当前内容区域并排显示
            comparison_image = np.hstack((ref_combined, marked_content))
            
            # 添加标题和说明
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(comparison_image, "Reference Regions", 
                       (10, 30), font, 1, (0, 255, 0), 2)
            cv2.putText(comparison_image, "Current Content (with disappearance)", 
                       (width + 10, 30), font, 1, (0, 255, 0), 2)
            
            return comparison_image

        except Exception as e:
            self.log(f"Error in create_comparison_visualization: {str(e)}")
            import traceback
            self.log(traceback.format_exc())
            raise

    def compute_disappearance_ratio(self, ref_region, current_content):
        """计算参考区域在当前内容中的消失度"""
        try:
            # 将区域分成多个小块（例如：10个）进行检测
            num_blocks = 10
            block_height = ref_region.shape[0] // num_blocks
            disappearance_count = 0
            
            # 对每个小块计算存在程度
            for i in range(num_blocks):
                start_y = i * block_height
                end_y = (i + 1) * block_height
                ref_block = ref_region[start_y:end_y]
                
                # 在当前内容中寻找这个小块
                block_found = False
                for offset in range(-30, 31):  # 小范围滑动窗口
                    curr_start = max(0, start_y + offset)
                    curr_end = min(current_content.shape[0], curr_start + block_height)
                    
                    if curr_end - curr_start < block_height:
                        continue
                        
                    curr_block = current_content[curr_start:curr_end]
                    if curr_block.shape[0] != ref_block.shape[0]:
                        curr_block = cv2.resize(curr_block, (ref_block.shape[1], ref_block.shape[0]))
                    
                    similarity = self.compute_similarity(ref_block, curr_block)
                    if similarity > 0.7:  # 较高的相似度阈值
                        block_found = True
                        break
                
                if not block_found:
                    disappearance_count += 1
            
            # 计算消失度
            disappearance_ratio = disappearance_count / num_blocks
            return disappearance_ratio
            
        except Exception as e:
            self.log(f"Error in compute_disappearance_ratio: {str(e)}")
            import traceback
            self.log(traceback.format_exc())
            raise

    def check_content_changed(self, reference_regions, current_frame):
        """检查参考内容是否真正消失"""
        try:
            ref_top, ref_mid, ref_bottom = reference_regions
            
            # 裁剪当前帧的内容区域
            content_start = self.fixed_top_height
            content_end = current_frame.shape[0] - self.fixed_bottom_height
            current_content = current_frame[content_start:content_end]
            
            # 计算每个区域的消失度
            disappearance_ratios = []
            for ref_region in [ref_top, ref_mid, ref_bottom]:
                ratio = self.compute_disappearance_ratio(ref_region, current_content)
                disappearance_ratios.append(ratio)
            
            # 记录消失度信息
            self.log(f"Disappearance ratios [top, mid, bot]: {disappearance_ratios}")
            
            # 创建可视化结果
            comparison_image = self.create_comparison_visualization(
                reference_regions, current_frame, disappearance_ratios)
            
            # 判断内容是否真正消失
            # 1. 顶部区域基本消失
            # 2. 中部区域大部分消失
            # 3. 底部区域开始消失
            # 4. 消失度呈递减趋势
            content_changed = (
                disappearance_ratios[0] > 0.9 and  # 顶部消失度 > 90%
                disappearance_ratios[1] > 0.7 and  # 中部消失度 > 70%
                disappearance_ratios[2] > 0.2 and  # 底部消失度 > 20%
                disappearance_ratios[0] > disappearance_ratios[1] > disappearance_ratios[2]  # 递减趋势
            )
            
            max_disappearance = max(disappearance_ratios)
            
            return content_changed, max_disappearance, comparison_image

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

