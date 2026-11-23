"""
Generate NSIS installer BMP assets for electron-builder.
header: 150x57 BMP (displayed top-right of installer pages)
sidebar: 164x314 BMP (displayed on the welcome/finish pages)
"""
import os, sys
try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit(1)

OUT = os.path.join("apps", "desktop", "assets")
os.makedirs(OUT, exist_ok=True)

NAVY = (30, 58, 138)
WHITE = (255, 255, 255)

def make_header():
    img = Image.new("RGB", (150, 57), NAVY)
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 14)
        small = ImageFont.truetype("arial.ttf", 9)
    except:
        font = small = ImageFont.load_default()
    draw.text((10, 12), "INCOME", fill=WHITE, font=font)
    draw.text((10, 32), "School Management System", fill=(180, 200, 255), font=small)
    return img

def make_sidebar():
    img = Image.new("RGB", (164, 314), NAVY)
    draw = ImageDraw.Draw(img)
    try:
        big  = ImageFont.truetype("arial.ttf", 24)
        med  = ImageFont.truetype("arial.ttf", 11)
        small = ImageFont.truetype("arial.ttf", 9)
    except:
        big = med = small = ImageFont.load_default()
    draw.text((20, 40),  "INCOME",   fill=WHITE,            font=big)
    draw.text((20, 80),  "School",   fill=(180, 200, 255),  font=med)
    draw.text((20, 97),  "Student",  fill=(180, 200, 255),  font=med)
    draw.text((20, 114), "Financial",fill=(180, 200, 255),  font=med)
    draw.text((20, 131), "System",   fill=(180, 200, 255),  font=med)
    draw.line([(20, 160), (144, 160)], fill=(255,255,255,80), width=1)
    draw.text((20, 174), "v1.0.0",   fill=(150,170,220),    font=small)
    return img

make_header().save(os.path.join(OUT, "installer-header.bmp"), "BMP")
make_sidebar().save(os.path.join(OUT, "installer-sidebar.bmp"), "BMP")
# installer icon is same as main icon — just copy
from shutil import copy2
copy2(os.path.join(OUT, "icon.ico"), os.path.join(OUT, "installer-icon.ico"))
print("Installer assets created.")
