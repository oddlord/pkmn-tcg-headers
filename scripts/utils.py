import io
import os
import json
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image

FONT_ENG = "Helvetica"
FONT_BOLD_ENG = "Helvetica-Bold"
FONT_JPN = "NotoSansJP"
FONT_BOLD_JPN = "NotoSansJP-Bold"

FONT_WEIGHT_REGULAR = "regular"
FONT_WEIGHT_BOLD = "bold"

V_ALIGN_TOP = "top"
V_ALIGN_MIDDLE = "middle"
V_ALIGN_BOTTOM = "bottom"
H_ALIGN_LEFT = "left"
H_ALIGN_CENTRE = "centre"
H_ALIGN_RIGHT = "right"

DEFAULT_TEXT_SIZE = 12

LOG_INDENT = "  "

# -*- coding:utf-8 -*-
ASIAN_CHAR_RANGES = [
  {"from": ord(u"\u3300"), "to": ord(u"\u33ff")},         # compatibility ideographs
  {"from": ord(u"\ufe30"), "to": ord(u"\ufe4f")},         # compatibility ideographs
  {"from": ord(u"\uf900"), "to": ord(u"\ufaff")},         # compatibility ideographs
  {"from": ord(u"\U0002F800"), "to": ord(u"\U0002fa1f")}, # compatibility ideographs
  {'from': ord(u'\u3040'), 'to': ord(u'\u309f')},         # Japanese Hiragana
  {"from": ord(u"\u30a0"), "to": ord(u"\u30ff")},         # Japanese Katakana
  {"from": ord(u"\u2e80"), "to": ord(u"\u2eff")},         # cjk radicals supplement
  {"from": ord(u"\u4e00"), "to": ord(u"\u9fff")},
  {"from": ord(u"\u3400"), "to": ord(u"\u4dbf")},
  {"from": ord(u"\U00020000"), "to": ord(u"\U0002a6df")},
  {"from": ord(u"\U0002a700"), "to": ord(u"\U0002b73f")},
  {"from": ord(u"\U0002b740"), "to": ord(u"\U0002b81f")},
  {"from": ord(u"\U0002b820"), "to": ord(u"\U0002ceaf")}  # included as of Unicode 8.0
]

frame_top_left_path = ""
frame_top_path = ""
frame_top_right_path = ""
frame_right_path = ""
frame_bottom_right_path = ""
frame_bottom_path = ""
frame_bottom_left_path = ""
frame_left_path = ""
frame_centre_path = ""


def init(fonts_dir_path, frame_imgs_dir_path):
    # Register Japanese fonts
    jp_title_font_path = os.path.join(fonts_dir_path, "NotoSansJP-Bold.ttf")
    pdfmetrics.registerFont(TTFont(FONT_BOLD_JPN, jp_title_font_path))
    jp_text_font_path = os.path.join(fonts_dir_path, "NotoSansJP-Regular.ttf")
    pdfmetrics.registerFont(TTFont(FONT_JPN, jp_text_font_path))

    global frame_top_left_path, frame_top_path, frame_top_right_path
    global frame_left_path, frame_centre_path, frame_right_path
    global frame_bottom_left_path, frame_bottom_path, frame_bottom_right_path
    frame_top_left_path = os.path.join(frame_imgs_dir_path, "frame-top-left.png")
    frame_top_path = os.path.join(frame_imgs_dir_path, "frame-top.png")
    frame_top_right_path = os.path.join(frame_imgs_dir_path, "frame-top-right.png")
    frame_right_path = os.path.join(frame_imgs_dir_path, "frame-right.png")
    frame_bottom_right_path = os.path.join(frame_imgs_dir_path, "frame-bottom-right.png")
    frame_bottom_path = os.path.join(frame_imgs_dir_path, "frame-bottom.png")
    frame_bottom_left_path = os.path.join(frame_imgs_dir_path, "frame-bottom-left.png")
    frame_left_path = os.path.join(frame_imgs_dir_path, "frame-left.png")
    frame_centre_path = os.path.join(frame_imgs_dir_path, "frame-centre.png")
    

# https://stackoverflow.com/questions/30069846/how-to-find-out-chinese-or-japanese-character-in-a-string-in-python
def text_contains_asian_chars(text):
  if not text:
      return False
  
  for char in text:
    is_asian_char = any([range["from"] <= ord(char) <= range["to"] for range in ASIAN_CHAR_RANGES])
    if is_asian_char:
      return True
    
  return False


def get_text_width(text, font_weight=FONT_WEIGHT_REGULAR, font_size=DEFAULT_TEXT_SIZE):
    font_name = get_font_name(text, font_weight)
    text_width = stringWidth(text, font_name, font_size)
    return text_width


def get_font_name(text, font_weight):
    has_asian_chars = text_contains_asian_chars(text)
    font_name = FONT_ENG
    if font_weight == FONT_WEIGHT_REGULAR and has_asian_chars:
        font_name = FONT_JPN
    elif font_weight == FONT_WEIGHT_BOLD and not has_asian_chars:
        font_name = FONT_BOLD_ENG
    elif font_weight == FONT_WEIGHT_BOLD and has_asian_chars:
        font_name = FONT_BOLD_JPN
    return font_name


def write_text(text, x, y, canvas, font_weight=FONT_WEIGHT_REGULAR, font_size=DEFAULT_TEXT_SIZE, h_align=H_ALIGN_LEFT, v_align=V_ALIGN_BOTTOM):
    if not text:
        return
    
    font_name = get_font_name(text, font_weight)
    canvas.setFont(font_name, font_size)
    text_width = stringWidth(text, font_name, font_size)

    # drawString takes the coordinates of the bottom-left of the text,
    # so we only need to adjust for centre/right and middle/top
    if h_align == H_ALIGN_CENTRE:
        x = x - (text_width / 2)
    elif h_align == H_ALIGN_RIGHT:
        x = x - text_width
    if v_align == V_ALIGN_MIDDLE:
        y = y - (font_size / 2)
    elif v_align == V_ALIGN_TOP:
        y = y - font_size

    canvas.drawString(x, y, text)


def draw_image(image_path, x, y, canvas, width=None, height=None, h_align=H_ALIGN_LEFT, v_align=V_ALIGN_BOTTOM, crop_to_cover=False):
    image = Image.open(image_path)
    if (crop_to_cover):
        image = crop_image_to_cover(image, width, height)

    image_io = get_image_io(image)

    image_w, image_h = image.size
    image_ratio = image_w / image_h

    if width:
        image_w = width
    elif height:
        image_w = image_h * image_ratio

    if height:
        image_h = height
    elif width:
        image_h = image_w / image_ratio

    # drawImage takes the coordinates of the bottom-left of the text,
    # so we only need to adjust for centre/right and middle/top
    if h_align == H_ALIGN_CENTRE:
        x = x - (image_w / 2)
    elif h_align == H_ALIGN_RIGHT:
        x = x - image_w
    if v_align == V_ALIGN_MIDDLE:
        y = y - (image_h / 2)
    elif v_align == V_ALIGN_TOP:
        y = y - image_h

    canvas.drawImage(image_io, x, y, width=image_w, height=image_h, mask='auto')


def draw_frame(x, y, canvas, width=400, height=150, border_thickness=10, h_align=H_ALIGN_LEFT, v_align=V_ALIGN_BOTTOM):
    full_w = width + 2*border_thickness
    full_h = height + 2*border_thickness

    # drawImage takes the coordinates of the bottom-left of the text,
    # so we only need to adjust for centre/right and middle/top
    #  We still need to adjust this as we want to take into consideration the full width/height of the frame
    if h_align == H_ALIGN_CENTRE:
        x = x - (full_w / 2)
    elif h_align == H_ALIGN_RIGHT:
        x = x - full_w
    if v_align == V_ALIGN_MIDDLE:
        y = y - (full_h / 2)
    elif v_align == V_ALIGN_TOP:
        y = y - full_h

    draw_image(frame_top_left_path, x, y+border_thickness+height, canvas, width=border_thickness, height=border_thickness)
    draw_image(frame_top_path, x+border_thickness, y+border_thickness+height, canvas, width=width, height=border_thickness)
    draw_image(frame_top_right_path, x+border_thickness+width, y+border_thickness+height, canvas, width=border_thickness, height=border_thickness)
    draw_image(frame_left_path, x, y+border_thickness, canvas, width=border_thickness, height=height)
    draw_image(frame_bottom_left_path, x, y, canvas, width=border_thickness, height=border_thickness)
    draw_image(frame_bottom_path, x+border_thickness, y, canvas, width=width, height=border_thickness)
    draw_image(frame_bottom_right_path, x+border_thickness+width, y, canvas, width=border_thickness, height=border_thickness)
    draw_image(frame_right_path, x+border_thickness+width, y+border_thickness, canvas, width=border_thickness, height=height)
    draw_image(frame_centre_path, x+border_thickness, y+border_thickness, canvas, width=width, height=height)


def get_image_io(image):
    image_data = io.BytesIO()
    image.save(image_data, format='png')
    image_data.seek(0)
    image_io = ImageReader(image_data)
    return image_io


def crop_image_to_cover(image, width, height):
    # Determine the aspect ratios of the image and the page
    image_width, image_height = image.size

    image_ratio = image_width / image_height
    box_ratio = width / height

    if image_ratio > box_ratio:
        # The image is too wide, crop horizontally
        new_image_width = int(image_height * box_ratio)
        left = (image_width - new_image_width) // 2
        right = left + new_image_width
        top, bottom = 0, image_height
    else:
        # The image is too tall, crop vertically
        new_image_height = int(image_width / box_ratio)
        top = (image_height - new_image_height) // 2
        bottom = top + new_image_height
        left, right = 0, image_width

    # Crop the image
    cropped_image = image.crop((left, top, right, bottom))
    return cropped_image


def parse_json(file_path):
    with open(file_path, encoding='utf-8') as f:
        txt = f.read()
        parsed = json.loads(txt)
    return parsed


def log(text, indent_level=0):
    log_text = ""
    for x in range(0, indent_level):
        log_text += LOG_INDENT
    log_text += text
    print(log_text)
