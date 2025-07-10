import io
import requests
from PIL import Image, ImageDraw, ImageFont
import discord
import os

FONT_PATH = os.path.join(os.path.dirname(__file__), "fonts", "DejaVuSans.ttf")

def get_font(font_size):
    try:
        return ImageFont.truetype(FONT_PATH, font_size)
    except Exception:
        return ImageFont.load_default()

def make_gallery_image(theme, date_str, user: discord.User, drawing_url):
    # Download user profile picture
    pfp_bytes = requests.get(user.display_avatar.url).content
    pfp = Image.open(io.BytesIO(pfp_bytes)).convert("RGBA").resize((64, 64))
    # Make circular mask for PFP
    mask = Image.new("L", (64, 64), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, 64, 64), fill=255)
    pfp.putalpha(mask)
    # Download drawing
    drawing_bytes = requests.get(drawing_url).content
    drawing = Image.open(io.BytesIO(drawing_bytes)).convert("RGBA")
    # Padding
    pad = 40
    # Fonts
    font_title = get_font(28)
    font_author = get_font(32)  # bigger author text
    # Title
    title = f"{theme} - {date_str}"
    # Calculate title width
    dummy_img = Image.new("RGBA", (1, 1))
    dummy_draw = ImageDraw.Draw(dummy_img)
    bbox = dummy_draw.textbbox((0, 0), title, font=font_title)
    title_w = bbox[2] - bbox[0]
    title_h = bbox[3] - bbox[1]
    # Calculate canvas size
    img_w, img_h = drawing.width, drawing.height
    # Padding
    pad = 40
    between_title_author = 20  # reduced vertical padding
    author_row_height = 64  # pfp height
    between_author_image = 40  # same as above
    top_extra = pad + title_h + between_title_author + author_row_height + between_author_image
    width = max(img_w + pad * 2, title_w + pad * 2)
    height = img_h + pad * 2 + top_extra
    # Create background
    bg = Image.new("RGBA", (width, height), (40, 40, 40, 255))
    draw_bg = ImageDraw.Draw(bg)
    # Draw title
    draw_bg.text(((width-title_w)//2, pad), title, font=font_title, fill=(255,255,255,255))
    # Author row
    author_y = pad + title_h + between_title_author
    pfp_x = (width - 64 - 40 - 200) // 2
    name_x = pfp_x + 64 + 40
    uname = user.display_name
    bbox2 = draw_bg.textbbox((0, 0), uname, font=font_author)
    uw, uh = bbox2[2] - bbox2[0], bbox2[3] - bbox2[1]
    draw_bg.text((name_x, author_y + (64-uh)//2), uname, font=font_author, fill=(255,255,255,255))  # white username
    bg.paste(pfp, (pfp_x, author_y), pfp)
    # Drawing (centered) with rounded rectangle border
    dx = (width - img_w) // 2
    dy = top_extra
    # Get most common color in drawing for border
    small = drawing.resize((32, 32)).convert('RGB')
    colors = small.getcolors(32*32)
    most_common = max(colors, key=lambda x: x[0])[1] if colors else (60, 60, 70)
    border_pad = 16
    border_rect = [dx - border_pad, dy - border_pad, dx + img_w + border_pad, dy + img_h + border_pad]
    radius = 32
    draw_bg.rounded_rectangle(border_rect, radius=radius, fill=most_common)
    bg.paste(drawing, (dx, dy), drawing)
    # Save to BytesIO
    out = io.BytesIO()
    bg.save(out, format="PNG")
    out.seek(0)
    return out

def make_theme_announcement_image(theme: str):
    width, height = 1000, 300
    bg = Image.new("RGBA", (width, height), (30, 30, 40, 255))
    draw = ImageDraw.Draw(bg)
    # Use bundled font
    font1 = get_font(36)
    font2 = get_font(54)
    # Title
    title = "Theme for today is:"
    bbox1 = draw.textbbox((0, 0), title, font=font1)
    w1, h1 = bbox1[2] - bbox1[0], bbox1[3] - bbox1[1]
    draw.text(((width-w1)//2, 70), title, font=font1, fill=(200,200,255,255))
    # Theme (colorful)
    bbox2 = draw.textbbox((0, 0), theme, font=font2)
    w2, h2 = bbox2[2] - bbox2[0], bbox2[3] - bbox2[1]
    draw.text(((width-w2)//2, 140), theme, font=font2, fill=(180,120,255,255))
    out = io.BytesIO()
    bg.save(out, format="PNG")
    out.seek(0)
    return out
