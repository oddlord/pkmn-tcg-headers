import io
import os
import json
import yaml
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from PIL import Image

FONT_ENG = "Font_ENG"
FONT_BOLD_ENG = "Font_ENG_Bold"
FONT_HANDWRITING_ENG = "Font_ENG_Handwriting"
FONT_JPN = "Font_JPN"
FONT_BOLD_JPN = "Font_JPN_Bold"
FONT_HANDWRITING_JPN = "Font_JPN_Handwriting"

FONT_WEIGHT_REGULAR = "regular"
FONT_WEIGHT_BOLD = "bold"
FONT_WEIGHT_HANDWRITING = "handwriting"

V_ALIGN_TOP = "top"
V_ALIGN_MIDDLE = "middle"
V_ALIGN_BOTTOM = "bottom"
H_ALIGN_LEFT = "left"
H_ALIGN_CENTRE = "centre"
H_ALIGN_RIGHT = "right"

DEFAULT_TEXT_SIZE = 12

LOG_INDENT = "  "

FRAME_BG_COLOUR_PLACEHOLDER = (255, 0, 0, 255)
FRAME_BG_COLOUR = (255, 255, 255, 200)
# Hack: need to shift each frame part by this amount in order to get rid of a miniscule gap
FRAME_PARTS_GAP = 0.08

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


def init(fonts_dir_path: str, frame_imgs_dir_path: str):
    # Register English fonts
    eng_regular_font_path = os.path.join(fonts_dir_path, "Roboto/Roboto-Regular.ttf")
    pdfmetrics.registerFont(TTFont(FONT_ENG, eng_regular_font_path))
    eng_bold_font_path = os.path.join(fonts_dir_path, "Roboto/Roboto-Bold.ttf")
    pdfmetrics.registerFont(TTFont(FONT_BOLD_ENG, eng_bold_font_path))
    eng_handwriting_font_path = os.path.join(fonts_dir_path, "PlaywriteGBS/PlaywriteGBS-Regular.ttf")
    pdfmetrics.registerFont(TTFont(FONT_HANDWRITING_ENG, eng_handwriting_font_path))
    # Register Japanese fonts
    jpn_regular_font_path = os.path.join(fonts_dir_path, "NotoSansJP/NotoSansJP-Regular.ttf")
    pdfmetrics.registerFont(TTFont(FONT_JPN, jpn_regular_font_path))
    jpn_bold_font_path = os.path.join(fonts_dir_path, "NotoSansJP/NotoSansJP-Bold.ttf")
    pdfmetrics.registerFont(TTFont(FONT_BOLD_JPN, jpn_bold_font_path))
    jpn_handwriting_font_path = os.path.join(fonts_dir_path, "HachiMaruPop/HachiMaruPop-Regular.ttf")
    pdfmetrics.registerFont(TTFont(FONT_HANDWRITING_JPN, jpn_handwriting_font_path))

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
def text_contains_asian_chars(text: str) -> bool:
  if not text:
      return False
  
  for char in text:
    is_asian_char = any([range["from"] <= ord(char) <= range["to"] for range in ASIAN_CHAR_RANGES])
    if is_asian_char:
      return True
    
  return False


def get_text_width(text: str, font_weight: str = FONT_WEIGHT_REGULAR, font_size: float = DEFAULT_TEXT_SIZE) -> float:
    font_name = get_font_name(text, font_weight)
    text_width = stringWidth(text, font_name, font_size)
    return text_width


def get_font_name(text: str, font_weight: str) -> str:
    if text_contains_asian_chars(text):
        if font_weight == FONT_WEIGHT_BOLD:
            return FONT_BOLD_JPN
        elif font_weight == FONT_WEIGHT_HANDWRITING:
            return FONT_HANDWRITING_JPN
        else:
            return FONT_JPN
    else:
        if font_weight == FONT_WEIGHT_BOLD:
            return FONT_BOLD_ENG
        elif font_weight == FONT_WEIGHT_HANDWRITING:
            return FONT_HANDWRITING_ENG
        else:
            return FONT_ENG


def write_text(text: str, x: float, y: float, canvas: Canvas, font_weight: str = FONT_WEIGHT_REGULAR, font_size: float = DEFAULT_TEXT_SIZE, h_align: str = H_ALIGN_LEFT, v_align: str = V_ALIGN_BOTTOM):
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


def draw_image(
        image_path: str, x: float, y: float, canvas: Canvas, width: float = None, height: float = None,
        h_align: str = H_ALIGN_LEFT, v_align: str = V_ALIGN_BOTTOM, crop_to_cover: bool = False,
        colour_placeholder = None, colour_new = None, border_width: float = 0):
    image = Image.open(image_path)
    if (crop_to_cover):
        image = crop_image_to_cover(image, width, height)

    image_w, image_h = image.size
    image_ratio = image_w / image_h

    if colour_placeholder and colour_new:
        for i in range(0, image_w):
            for j in range(0, image_h):
                current_pixel_colour = image.getpixel((i, j))
                if (current_pixel_colour == colour_placeholder):
                    image.putpixel((i, j), colour_new)

    if width:
        image_w = width
    elif height:
        image_w = height * image_ratio

    if height:
        image_h = height
    elif width:
        image_h = width / image_ratio

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

    image_io = get_image_io(image)
    canvas.drawImage(image_io, x, y, width=image_w, height=image_h, mask='auto')

    if border_width > 0:
        canvas.setLineWidth(border_width)
        canvas.setStrokeColorRGB(0, 0, 0)
        canvas.rect(x, y, image_w, image_h, stroke=1, fill=0)

    return image_w, image_h


def draw_frame(x: float, y: float, canvas: Canvas, width: float = 400, height: float = 150, border_thickness: float= 10, h_align: str = H_ALIGN_LEFT, v_align: str = V_ALIGN_BOTTOM, is_full_size: bool = False):
    if (is_full_size):
        width = width - 2*border_thickness
        height = height - 2*border_thickness

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

    centre_width = width + 2*FRAME_PARTS_GAP
    left_x = x
    centre_x = left_x + border_thickness - FRAME_PARTS_GAP
    right_x = centre_x + centre_width - FRAME_PARTS_GAP

    middle_height = height + 2*FRAME_PARTS_GAP
    bottom_y = y
    middle_y = bottom_y + border_thickness - FRAME_PARTS_GAP
    top_y = middle_y + middle_height - FRAME_PARTS_GAP

    draw_frame_image(frame_top_left_path, left_x, top_y, canvas, width=border_thickness, height=border_thickness)
    draw_frame_image(frame_top_path, centre_x, top_y, canvas, width=centre_width, height=border_thickness)
    draw_frame_image(frame_top_right_path, right_x, top_y, canvas, width=border_thickness, height=border_thickness)
    draw_frame_image(frame_left_path, left_x, middle_y, canvas, width=border_thickness, height=middle_height)
    draw_frame_image(frame_bottom_left_path, left_x, bottom_y, canvas, width=border_thickness, height=border_thickness)
    draw_frame_image(frame_bottom_path, centre_x, bottom_y, canvas, width=centre_width, height=border_thickness)
    draw_frame_image(frame_bottom_right_path, right_x, bottom_y, canvas, width=border_thickness, height=border_thickness)
    draw_frame_image(frame_right_path, right_x, middle_y, canvas, width=border_thickness, height=middle_height)
    draw_frame_image(frame_centre_path, centre_x, middle_y, canvas, width=centre_width, height=middle_height)


def draw_frame_image(image_path, x, y, canvas, width, height):
    draw_image(image_path, x, y, canvas, width=width, height=height, colour_placeholder=FRAME_BG_COLOUR_PLACEHOLDER, colour_new=FRAME_BG_COLOUR)


def get_image_io(image: Image) -> ImageReader:
    image_data = io.BytesIO()
    image.save(image_data, format='png')
    image_data.seek(0)
    image_io = ImageReader(image_data)
    return image_io


def crop_image_to_cover(image: Image, width: float, height: float) -> Image:
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


def parse_json(file_path: str) -> dict:
    with open(file_path, encoding='utf-8') as f:
        txt = f.read()
        parsed = json.loads(txt)
    return parsed


def parse_yaml(file_path: str) -> dict:
    with open(file_path, "r") as f:
        parsed = yaml.safe_load(f)
    return parsed


def log(text: str, indent_level: int = 0):
    log_text = ""
    for x in range(0, indent_level):
        log_text += LOG_INDENT
    log_text += text
    print(log_text)
