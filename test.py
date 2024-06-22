import requests


def pnl(text):
    url = f"https://textoverimage.moesif.com/image?image_url=https%3A%2F%2Fres.cloudinary.com%2Fdb1owt5ev%2Fimage%2Fupload%2Fv1718973675%2Fgmfrezafjuq16fq3vwfr.jpg&text={text}25&text_color={'20ee19ff' if text > 0 else 'f7190dff'}&text_size=128&margin=&y_align=middle&x_align=right"
    return url



print(pnl(0))


