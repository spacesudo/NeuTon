from PIL import Image, ImageDraw, ImageFont
import random

def pnlimg():
    images = {
        "1": "pnl1.jpg",
        "2": "pnl2.jpg",
        "3": "pnl3.jpg",
        "4": "pnl4.jpg"
    }

def pnl_pic(text1, text2: str, userid: int):
    image = Image.open('pnl2.jpg')

    img_width, img_height = image.size

    draw = ImageDraw.Draw(image)

    text1 = f"{text1} %"
    font_path = 'pixel.ttf'
    font_size = 120
    font = ImageFont.truetype(font_path, font_size)

    # Drawing the first text
    bbox1 = draw.textbbox((0, 0), text1, font=font)
    text_width1 = bbox1[2] - bbox1[0]
    text_height1 = bbox1[3] - bbox1[1]

    x1 = img_width - text_width1 - 10  
    y1 = (img_height - text_height1) // 2

    draw.text((x1, y1), text1, font=font, fill='lawngreen')

    # Drawing the second text "Dave"
    text2 = text2
    font_path = 'pixel.ttf'
    font_size = 50
    font = ImageFont.truetype(font_path, font_size)

    bbox2 = draw.textbbox((0, 0), text2, font=font)
    text_width2 = bbox2[2] - bbox2[0]
    text_height2 = bbox2[3] - bbox2[1]

    x2 = img_width - text_width2 - 10  
    y2 = img_height - text_height2 - 10  # Bottom right corner with a 10 pixel margin

    draw.text((x2, y2), text2, font=font, fill='lawngreen')

    image.save(f'media/output_image{userid}.jpg')
    

pnl_pic(500, "Test", 122)