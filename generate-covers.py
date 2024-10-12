import io
import os
import json
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image

# Links:
# https://bulbapedia.bulbagarden.net/wiki/List_of_Pok%C3%A9mon_Trading_Card_Game_expansions
# https://bulbapedia.bulbagarden.net/wiki/List_of_Japanese_Pok%C3%A9mon_Trading_Card_Game_expansions

# TODO!!!
# Go through the collection and move the JP cards to their own set
# Add a regions list in the JSON to specify "eng" and/or "jpn"
# Refactor!!!!!
# https://stackoverflow.com/questions/30069846/how-to-find-out-chinese-or-japanese-character-in-a-string-in-python

CATALOG_DIR_PATH = "assets/catalog"
IMGS_DIR_PATH = "assets/imgs"
FONTS_DIR_PATH = "assets/fonts"

OUTPUT_FILENAME = "covers.pdf"
CATALOG_FILENAME = "catalog.json"
FRAME_FILENAME = "frame.png"

REGION_FILENAMES = {
    # "all": "jpn-eng.jpg",
    "all": "eng-jpn.jpg",
    "eng": "eng.png",
    "jpn": "jpn.jpg"
}

COVER_FILENAME_PREFIX = "cover"
SYMBOL_FILENAME_PREFIX = "symbol"

SET_LOG_INDENT = "  "

FRAME_WIDTH = 300
FRAME_PADDING = 25
TEXT_PADDING = 10
SYMBOL_WIDTH = 20
SYMBOL_PADDING = 2.5

TITLE_SIZE = 16
TEXT_SIZE = 12

FONT_ENG = "Helvetica"
FONT_BOLD_ENG = "Helvetica-Bold"
FONT_JPN = "NotoSansJP"
FONT_BOLD_JPN = "NotoSansJP-Bold"

V_ALIGN_TOP = "top"
V_ALIGN_MIDDLE = "middle"
V_ALIGN_BOTTOM = "bottom"
H_ALIGN_LEFT = "left"
H_ALIGN_CENTRE = "centre"
H_ALIGN_RIGHT = "right"

ID_KEY = "id"
NAME_KEY = "name"
SETS_KEY = "sets"
DATE_KEY = "date"
REGION_KEY = "region"
NAME_ALT_KEY = "name_alt"

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


def generate_pdf(series, img_dir_path, catalog_dir_path, output_path):
    page_size = A4
    page_width, page_height = page_size

    # Create a new PDF document
    c = canvas.Canvas(output_path, pagesize=A4)
        
    frame_img_path = os.path.join(img_dir_path, FRAME_FILENAME)
    frame_img = Image.open(frame_img_path)
    frame_img_io = get_image_io(frame_img)

    frame_width, frame_height = frame_img.size
    frame_ratio = frame_width / frame_height
    frame_width, frame_height = (FRAME_WIDTH, FRAME_WIDTH / frame_ratio)
    frame_x, frame_y = (page_width - frame_width - FRAME_PADDING, page_height - frame_height - FRAME_PADDING)

    frame_left_x = frame_x
    frame_top_y = frame_y + frame_height
    frame_right_x = frame_x + frame_width
    frame_bottom_y = frame_y

    padded_frame_left_x = frame_left_x + TEXT_PADDING
    padded_frame_top_y = frame_top_y - TEXT_PADDING
    padded_frame_right_x = frame_right_x - TEXT_PADDING
    padded_frame_bottom_y = frame_bottom_y +TEXT_PADDING

    frame_centre_x = frame_left_x + frame_width/2
    frame_centre_y = frame_bottom_y + frame_height/2

    page = 0
    for serie in series:
        print("")

        if ID_KEY not in serie:
            print("Missing serie ID. Skipping.")
            continue

        serie_id = serie[ID_KEY]
        serie_dir_path = os.path.join(catalog_dir_path, serie_id)
        if not os.path.isdir(serie_dir_path):
            print(f"Missing folder for serie with ID \"{serie_id}\". Skipping.")
            continue

        serie_name = None
        if NAME_KEY in serie:
            serie_name = serie[NAME_KEY]

        serie_print_name = serie_name or f"<{serie_id}>"
        print(f"{serie_print_name}")

        sets = []
        if SETS_KEY in serie:
            sets = serie[SETS_KEY]

        for set in sets:
            if ID_KEY not in set:
                print(f"{SET_LOG_INDENT}Missing set ID. Skipping.")
                continue

            set_id = set[ID_KEY]
            set_dir_path = os.path.join(serie_dir_path, set_id)
            if not os.path.isdir(set_dir_path):
                print(f"{SET_LOG_INDENT}Missing folder for set with ID \"{set_id}\". Skipping.")
                continue

            if NAME_KEY not in set:
                print(f"{SET_LOG_INDENT}Missing name for set with ID \"{set_id}\". Skipping.")
                continue
            set_name = set[NAME_KEY]

            has_name_alt = NAME_ALT_KEY in set
            if has_name_alt:
                set_name_alt = set[NAME_ALT_KEY]

            if DATE_KEY not in set:
                print(f"{SET_LOG_INDENT}Missing date for set with ID \"{set_id}\". Skipping.")
                continue
            set_date = set[DATE_KEY]

            set_files = os.listdir(set_dir_path)
            set_cover_path = None
            set_symbol_paths = []
            for file in set_files:
                if file.startswith(f"{COVER_FILENAME_PREFIX}."):
                    set_cover_path = os.path.join(set_dir_path, file)
                if file.startswith(f"{SYMBOL_FILENAME_PREFIX}"):
                    symbol_path = os.path.join(set_dir_path, file)
                    set_symbol_paths.append(symbol_path)

            if not set_cover_path:
                print(f"{SET_LOG_INDENT}Missing cover for set with ID \"{set_id}\". Skipping.")
                continue

            page = page + 1
            set_print_str = f"  {page}. {set_name}"
            if has_name_alt:
                set_print_str += f" ({set_name_alt})"
            print(set_print_str)

            # Set the background image for the current page
            cropped_img = crop_image_to_cover(set_cover_path, page_size)
            cropped_img_io = get_image_io(cropped_img)
            c.drawImage(cropped_img_io, 0, 0, width=page_width, height=page_height)

            # Draw the frame
            c.drawImage(frame_img_io, frame_x, frame_y, width=frame_width, height=frame_height, mask='auto', preserveAspectRatio=True)

            # Write the set's name (and alternative name, if present)
            title_y = frame_centre_y
            if has_name_alt:
                title_y = frame_centre_y + TEXT_SIZE/2
                subtitle_y = frame_centre_y - TITLE_SIZE/2
                write_text(set_name_alt, frame_centre_x, subtitle_y, c, h_align=H_ALIGN_CENTRE, v_align=V_ALIGN_MIDDLE)
            title_font = FONT_BOLD_ENG
            if text_contains_asian_chars(set_name):
                title_font = FONT_BOLD_JPN
            write_text(set_name, frame_centre_x, title_y, c, title_font, TITLE_SIZE, H_ALIGN_CENTRE, V_ALIGN_MIDDLE)

            # Write the serie name in the top-left corner, if present
            if serie_name:
                write_text(serie_name, padded_frame_left_x, padded_frame_top_y, c, h_align=H_ALIGN_LEFT, v_align=V_ALIGN_TOP)

            # Write the date in the bottom-right corner
            write_text(set_date, frame_right_x - TEXT_PADDING, frame_bottom_y + TEXT_PADDING, c, h_align=H_ALIGN_RIGHT, v_align=V_ALIGN_BOTTOM)

            # Draw the symbol(s)
            symbol_x = padded_frame_left_x
            for symbol_path in set_symbol_paths:
                draw_symbol(symbol_path, symbol_x, padded_frame_bottom_y, c)
                symbol_x = symbol_x + get_symbol_width(symbol_path) + SYMBOL_PADDING

            # Draw the region symbol, if specify
            if REGION_KEY in set:
                set_region = set[REGION_KEY]
                if set_region in REGION_FILENAMES:
                    region_filename = REGION_FILENAMES[set_region]
                    region_path = os.path.join(IMGS_DIR_PATH, region_filename)
                    draw_symbol(region_path, padded_frame_right_x, padded_frame_top_y, c, h_align=H_ALIGN_RIGHT, v_align=V_ALIGN_TOP)

            # Add a new page
            c.showPage()

    # Save and close the PDF document
    c.save()


# https://stackoverflow.com/questions/30069846/how-to-find-out-chinese-or-japanese-character-in-a-string-in-python
def text_contains_asian_chars(text):
  for char in text:
    is_asian_char = any([range["from"] <= ord(char) <= range["to"] for range in ASIAN_CHAR_RANGES])
    if is_asian_char:
      return True
  return False


def write_text(text, x, y, canvas, font_name=FONT_ENG, font_size=TEXT_SIZE, h_align=H_ALIGN_LEFT, v_align=V_ALIGN_BOTTOM):
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

    symbol_width, symbol_height = symbol_image.size
    symbol_ratio = symbol_width / symbol_height
    symbol_width, symbol_height = (SYMBOL_WIDTH, SYMBOL_WIDTH / symbol_ratio)

    # drawImage takes the coordinates of the bottom-left of the text,
    # so we only need to adjust for centre/right and middle/top

    if h_align == H_ALIGN_CENTRE:
        x = x - (symbol_width / 2)
    elif h_align == H_ALIGN_RIGHT:
        x = x - symbol_width

    if v_align == V_ALIGN_MIDDLE:
        y = y - (symbol_height / 2)
    elif v_align == V_ALIGN_TOP:
        y = y - symbol_height

    canvas.drawImage(symbol_image_io, x, y, width=symbol_width, height=symbol_height, mask='auto')


def get_symbol_width(symbol_path):
    symbol_image = Image.open(symbol_path)
    symbol_width, symbol_height = symbol_image.size
    symbol_ratio = symbol_width / symbol_height
    symbol_width, symbol_height = (SYMBOL_WIDTH, SYMBOL_WIDTH / symbol_ratio)
    return symbol_width


def crop_image_to_cover(image_path, page_size):
    # Open the image
    image = Image.open(image_path)

    # Determine the aspect ratios of the image and the page
    image_width, image_height = image.size
    page_width, page_height = page_size

    image_ratio = image_width / image_height
    page_ratio = page_width / page_height

    if image_ratio > page_ratio:
        # The image is too wide, crop horizontally
        new_image_width = int(image_height * page_ratio)
        left = (image_width - new_image_width) // 2
        right = left + new_image_width
        top, bottom = 0, image_height
    else:
        # The image is too tall, crop vertically
        new_image_height = int(image_width / page_ratio)
        top = (image_height - new_image_height) // 2
        bottom = top + new_image_height
        left, right = 0, image_width

    # Crop the image
    cropped_image = image.crop((left, top, right, bottom))

    return cropped_image


def get_image_io(image):
    image_data = io.BytesIO()
    image.save(image_data, format='png')
    image_data.seek(0)
    image_io = ImageReader(image_data)
    return image_io


def read_catalog_from_json(file_path):
    with open(file_path, encoding='utf-8') as f:
        txt = f.read()
        catalog = json.loads(txt)
    return catalog


# Get the directory path of the script
script_directory = os.path.dirname(os.path.abspath(__file__))

# Get paths
json_file_path = os.path.join(script_directory, CATALOG_FILENAME)
output_file_path = os.path.join(script_directory, OUTPUT_FILENAME)
img_dir_path = os.path.join(script_directory, IMGS_DIR_PATH)
fonts_dir_path = os.path.join(script_directory, FONTS_DIR_PATH)
catalog_dir_path = os.path.join(script_directory, CATALOG_DIR_PATH)

# Register Japanese fonts
jp_title_font_path = os.path.join(fonts_dir_path, "NotoSansJP-Bold.ttf")
pdfmetrics.registerFont(TTFont(FONT_BOLD_JPN, jp_title_font_path))
jp_text_font_path = os.path.join(fonts_dir_path, "NotoSansJP-Regular.ttf")
pdfmetrics.registerFont(TTFont(FONT_JPN, jp_text_font_path))

# Parse the catalog data from the JSON file to a dictionary
catalog = read_catalog_from_json(json_file_path)

# Generate the PDF
generate_pdf(catalog, img_dir_path, catalog_dir_path, output_file_path)
