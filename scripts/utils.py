import io
import os
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

default_text_size = 0
symbol_width = 0


def init(script_directory, fonts_dir_path, text_size_default, symbol_w):
    # Register Japanese fonts
    fonts_dir_path = os.path.join(script_directory, fonts_dir_path)
    jp_title_font_path = os.path.join(fonts_dir_path, "NotoSansJP-Bold.ttf")
    pdfmetrics.registerFont(TTFont(FONT_BOLD_JPN, jp_title_font_path))
    jp_text_font_path = os.path.join(fonts_dir_path, "NotoSansJP-Regular.ttf")
    pdfmetrics.registerFont(TTFont(FONT_JPN, jp_text_font_path))

    global default_text_size, symbol_width
    default_text_size = text_size_default
    symbol_width = symbol_w
    

# https://stackoverflow.com/questions/30069846/how-to-find-out-chinese-or-japanese-character-in-a-string-in-python
def text_contains_asian_chars(text):
  if not text:
      return False
  
  for char in text:
    is_asian_char = any([range["from"] <= ord(char) <= range["to"] for range in ASIAN_CHAR_RANGES])
    if is_asian_char:
      return True
    
  return False


def get_text_width(text, font_weight=FONT_WEIGHT_REGULAR, font_size=None):
    if not font_size:
        font_size = default_text_size
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


def write_text(text, x, y, canvas, font_weight=FONT_WEIGHT_REGULAR, font_size=None, h_align=H_ALIGN_LEFT, v_align=V_ALIGN_BOTTOM):
    if not text:
        return
    
    if not font_size:
        font_size = default_text_size
    
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


def draw_symbol(symbol_path, x, y, canvas, h_align=H_ALIGN_LEFT, v_align=V_ALIGN_BOTTOM):
    symbol_image = Image.open(symbol_path)
    symbol_image_io = get_image_io(symbol_image)

    symbol_w, symbol_h = symbol_image.size
    symbol_ratio = symbol_w / symbol_h
    symbol_w, symbol_h = (symbol_width, symbol_width / symbol_ratio)

    # drawImage takes the coordinates of the bottom-left of the text,
    # so we only need to adjust for centre/right and middle/top

    if h_align == H_ALIGN_CENTRE:
        x = x - (symbol_w / 2)
    elif h_align == H_ALIGN_RIGHT:
        x = x - symbol_w

    if v_align == V_ALIGN_MIDDLE:
        y = y - (symbol_h / 2)
    elif v_align == V_ALIGN_TOP:
        y = y - symbol_h

    canvas.drawImage(symbol_image_io, x, y, width=symbol_w, height=symbol_h, mask='auto')


def get_image_io(image):
    image_data = io.BytesIO()
    image.save(image_data, format='png')
    image_data.seek(0)
    image_io = ImageReader(image_data)
    return image_io
