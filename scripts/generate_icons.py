"""
Generate application icons for INCOME.
Produces PNG icons of various sizes and an ICO file.
Run from the project root:
  python scripts/generate_icons.py
"""

import os
import sys

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Pillow not found. Install with: pip install Pillow")
    sys.exit(1)

# INCOME brand colors
BG_COLOR = (30, 58, 138)       # #1e3a8a — deep navy
TEXT_COLOR = (255, 255, 255)   # white

SIZES_PNG = [72, 96, 128, 144, 152, 192, 256, 384, 512]
ICO_SIZES  = [16, 32, 48, 64, 128, 256]

ICONS_DIR_WEB = os.path.join("apps", "web", "public", "icons")
ICONS_DIR_ELK = os.path.join("apps", "desktop", "assets")

os.makedirs(ICONS_DIR_WEB, exist_ok=True)
os.makedirs(ICONS_DIR_ELK, exist_ok=True)


def make_icon(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Rounded square background
    radius = size // 7
    draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=BG_COLOR)

    # Text "INC"
    font_size = size // 3
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except OSError:
        font = ImageFont.load_default()

    text = "INC"
    bbox = draw.textbbox((0, 0), text, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (size - w) // 2 - bbox[0]
    y = (size - h) // 2 - bbox[1]
    draw.text((x, y), text, fill=TEXT_COLOR, font=font)

    return img


# Generate PWA icon PNGs
for s in SIZES_PNG:
    img = make_icon(s)
    out = os.path.join(ICONS_DIR_WEB, f"icon-{s}x{s}.png")
    img.save(out, "PNG")
    print(f"  Created {out}")

# Generate Electron ICO
ico_images = [make_icon(s).convert("RGBA") for s in ICO_SIZES]
ico_path = os.path.join(ICONS_DIR_ELK, "icon.ico")
ico_images[-1].save(ico_path, format="ICO", sizes=[(s, s) for s in ICO_SIZES])
print(f"  Created {ico_path}")

# Also save a 256px PNG for electron-builder
png_path = os.path.join(ICONS_DIR_ELK, "icon.png")
make_icon(256).save(png_path, "PNG")
print(f"  Created {png_path}")

print("\nAll icons generated successfully.")
