import os
from PIL import Image, ImageDraw, ImageFont

def generate():
    """生成记忆占位图（适配脚本调用）"""
    ocr_core_dir = os.path.join("Y_OCR库", "核心记忆")
    os.makedirs(ocr_core_dir, exist_ok=True)
    
    img = Image.new("RGB", (400, 200), color="#f5f5f5")
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default(size=24)
    draw.text((50, 70), "核心_存在公理_1", fill="#333333", font=font)
    draw.line((20, 150, 380, 150), fill="#cccccc", width=1)
    draw.text((50, 160), "初始核心记忆占位", fill="#666666", font=ImageFont.load_default(size=16))
    
    img_path = os.path.join(ocr_core_dir, "核心_存在公理_1.png")
    img.save(img_path)
    print(f"✅ 占位图片生成完成：{img_path}")