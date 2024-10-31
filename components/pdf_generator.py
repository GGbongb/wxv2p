from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from PIL import Image
from reportlab.lib.utils import ImageReader
from PyQt5.QtCore import QBuffer
import io

class PDFGenerator:
    def __init__(self):
        # A4纸张尺寸（横向）
        self.page_width, self.page_height = A4
        
        # 设置页面边距（10mm）
        self.margin = 10 * mm
        
        # 图片间距（5mm）
        self.image_spacing = 5 * mm
        
        # 计算可用区域
        self.usable_width = self.page_width - (2 * self.margin)
        self.usable_height = self.page_height - (2 * self.margin)
        
        # 计算单个图片的最大宽度（考虑间距）
        self.image_width = (self.usable_width - (2 * self.image_spacing)) / 3

    def generate_pdf(self, images, output_path):
        """
        生成PDF文件
        :param images: QImage列表
        :param output_path: PDF保存路径
        """
        try:
            # 创建PDF文档
            c = canvas.Canvas(output_path, pagesize=A4)
            
            # 处理所有图片
            for i in range(0, len(images), 3):
                # 获取当前页的图片组（最多3张）
                page_images = images[i:i+3]
                
                # 在PDF中绘制图片
                x = self.margin  # 起始x坐标
                for img in page_images:
                    # 将QImage转换为PIL Image
                    buffer = QBuffer()
                    buffer.open(QBuffer.ReadWrite)
                    img.save(buffer, "PNG")
                    pil_img = Image.open(io.BytesIO(buffer.data()))
                    
                    # 计算图片缩放后的高度（保持宽高比）
                    aspect_ratio = pil_img.height / pil_img.width
                    image_height = self.image_width * aspect_ratio
                    
                    # 确保图片高度不超过可用高度
                    if image_height > self.usable_height:
                        image_height = self.usable_height
                        image_width_adjusted = image_height / aspect_ratio
                    else:
                        image_width_adjusted = self.image_width
                    
                    # 计算y坐标使图片垂直居中
                    y = self.margin + (self.usable_height - image_height) / 2
                    
                    # 将图片绘制到PDF
                    c.drawImage(
                        ImageReader(pil_img),
                        x,
                        y,
                        width=image_width_adjusted,
                        height=image_height
                    )
                    
                    # 更新x坐标（加上图片宽度和间距）
                    x += image_width_adjusted + self.image_spacing
                
                # 添加新页面（除非是最后一页）
                if i + 3 < len(images):
                    c.showPage()
            
            # 保存PDF
            c.save()
            return True, None
            
        except Exception as e:
            return False, str(e)