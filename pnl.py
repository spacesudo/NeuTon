from PIL import Image, ImageDraw, ImageFont
import random

def pnlwin():
    images = {
        "1": "pnlwin1.png",
        "2": "pnlwin2.png",
    }
    
    random_key = random.choice(list(images.keys()))
    
    selected = images[random_key]
    
    return selected

def pnlloss():
    images = {
        "1": "pnlloss1.png",
        "2": "pnlloss2.png",
    }
    
    random_key = random.choice(list(images.keys()))
    
    selected = images[random_key]
    
    return selected

def pnlpic(pnl: int, symbol: str, invest: int, worth: int, userid: int):
    
    img = pnlloss() if pnl < 0 else pnlwin()
    
    image = Image.open(img)
    draw = ImageDraw.Draw(image)

    top_left_text = f"${symbol}/TON"
    font_path = 'semi.ttf'
    font_size = 100
    font = ImageFont.truetype(font_path, font_size)

    x_top_left = 10
    y_top_left = 10

    # Define the color "#1bc416"
    color = "#c41616" if pnl < 0 else "#1bc416"

    # Draw the top left text
    draw.text((x_top_left, y_top_left), top_left_text, font=font, fill=color)

    # Define the middle left texts
    middle_left_text_1 = f"      {pnl}%"
    middle_left_text_2 = f"\n\n   Invested: {invest} Ton \n   Worth: {worth} Ton"
    font_size_middle_left_1 = 200
    font_size_middle_left_2 = 60
    font_middle_left_1 = ImageFont.truetype(font_path, font_size_middle_left_1)
    font_middle_left_2 = ImageFont.truetype(font_path, font_size_middle_left_2)

    # Calculate the middle left text positions
    bbox_middle_left_1 = draw.textbbox((0, 0), middle_left_text_1, font=font_middle_left_1)
    text_width_middle_left_1 = bbox_middle_left_1[2] - bbox_middle_left_1[0]
    text_height_middle_left_1 = bbox_middle_left_1[3] - bbox_middle_left_1[1]

    bbox_middle_left_2 = draw.textbbox((0, 0), middle_left_text_2, font=font_middle_left_2)
    text_height_middle_left_2 = bbox_middle_left_2[3] - bbox_middle_left_2[1]

    x_middle_left_1 = 10
    x_middle_left_2 = 10
    y_middle_left_1 = (image.height - (text_height_middle_left_1 + text_height_middle_left_2 + 20)) // 2
    y_middle_left_2 = y_middle_left_1 + text_height_middle_left_1 + 20

    # Draw the middle left texts
    draw.text((x_middle_left_1, y_middle_left_1), middle_left_text_1, font=font_middle_left_1, fill=color)
    draw.text((x_middle_left_2, y_middle_left_2), middle_left_text_2, font=font_middle_left_2, fill=color)

    image.save(f'media/output{userid}.jpg')
    
if __name__ == "__main__":    
    pnlpic(1050, 'nigger', 8,5,22)