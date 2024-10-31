from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from PIL import Image
from reportlab.lib.utils import ImageReader
from PyQt5.QtCore import QBuffer
import io
import logging

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PDFGenerator:
    def __init__(self):
        # A4纸张尺寸（横向）
        self.page_width, self.page_height = landscape(A4)
        logger.info(f"初始化PDF生成器 - 页面尺寸: {self.page_width/mm:.1f}mm x {self.page_height/mm:.1f}mm")
        
        # 设置页面边距（5mm）
        self.margin = 5 * mm
        
        # 图片间距（3mm）
        self.image_spacing = 3 * mm
        
        # 计算可用区域
        self.usable_width = self.page_width - (2 * self.margin)
        self.usable_height = self.page_height - (2 * self.margin)
        logger.info(f"可用区域: {self.usable_width/mm:.1f}mm x {self.usable_height/mm:.1f}mm")
        
        # 计算单个图片的最大宽度
        self.image_width = (self.usable_width - (2 * self.image_spacing)) / 3
        logger.info(f"单个图片最大宽度: {self.image_width/mm:.1f}mm")

    def generate_pdf(self, images, output_path):
        try:
            logger.info(f"开始生成PDF - 总图片数: {len(images)}")
            logger.info(f"输出路径: {output_path}")
            
            # 创建横向PDF文档
            c = canvas.Canvas(output_path, pagesize=landscape(A4))
            logger.info("创建PDF画布成功")
            
            # 处理所有图片
            for page_num, i in enumerate(range(0, len(images), 3)):
                logger.info(f"\n处理第 {page_num + 1} 页")
                page_images = images[i:i+3]
                logger.info(f"当前页面图片数: {len(page_images)}")
                
                # 计算每个图片的尺寸和位置
                image_positions = []
                max_height = self.usable_height
                
                # 计算图片宽度（考虑间距）
                available_width = self.usable_width - (self.image_spacing * 2)
                single_width = available_width / 3
                logger.info(f"单个图片计算宽度: {single_width/mm:.1f}mm")
                
                # 计算起始X坐标
                start_x = self.margin
                logger.info(f"起始X坐标: {start_x/mm:.1f}mm")
                
                # 处理每张图片
                for idx, img in enumerate(page_images):
                    logger.info(f"\n处理第 {idx + 1} 张图片")
                    
                    # 转换图片
                    buffer = QBuffer()
                    buffer.open(QBuffer.ReadWrite)
                    img.save(buffer, "PNG")
                    pil_img = Image.open(io.BytesIO(buffer.data()))
                    
                    # 获取原始尺寸
                    original_width, original_height = pil_img.size
                    logger.info(f"原始图片尺寸: {original_width}px x {original_height}px")
                    
                    # 计算缩放后的尺寸
                    aspect_ratio = original_height / original_width
                    scaled_height = single_width * aspect_ratio
                    logger.info(f"纵横比: {aspect_ratio:.2f}")
                    logger.info(f"缩放后高度: {scaled_height/mm:.1f}mm")
                    
                    if scaled_height > max_height:
                        logger.info("图片高度超出限制，进行调整")
                        scaled_height = max_height
                        single_width = scaled_height / aspect_ratio
                        logger.info(f"调整后宽度: {single_width/mm:.1f}mm")
                    
                    # 计算坐标
                    y = self.margin + (self.usable_height - scaled_height) / 2
                    x = start_x + (idx * (single_width + self.image_spacing))
                    logger.info(f"图片位置: x={x/mm:.1f}mm, y={y/mm:.1f}mm")
                    
                    image_positions.append({
                        'image': pil_img,
                        'x': x,
                        'y': y,
                        'width': single_width,
                        'height': scaled_height
                    })
                
                # 绘制图片
                logger.info("\n开始绘制图片到PDF")
                for idx, pos in enumerate(image_positions):
                    logger.info(f"绘制第 {idx + 1} 张图片")
                    logger.info(f"绘制参数: x={pos['x']/mm:.1f}mm, y={pos['y']/mm:.1f}mm, "
                              f"width={pos['width']/mm:.1f}mm, height={pos['height']/mm:.1f}mm")
                    c.drawImage(
                        ImageReader(pos['image']),
                        pos['x'],
                        pos['y'],
                        width=pos['width'],
                        height=pos['height']
                    )
                
                # 添加新页面
                if i + 3 < len(images):
                    logger.info("添加新页面")
                    c.showPage()
            
            # 保存PDF
            logger.info("\n保存PDF文件")
            c.save()
            logger.info("PDF生成成功")
            return True, None
            
        except Exception as e:
            logger.error(f"PDF生成失败: {str(e)}", exc_info=True)
            return False, str(e)