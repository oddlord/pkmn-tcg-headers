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

OUTPUT_FILENAME = "covers.pdf"
CATALOG_FILENAME = "catalog.json"
IMG_FOLDER_PATH = "assets/img"
FONTS_FOLDER_PATH = "assets/fonts"
FRAME_FILENAME = "frame.png"

FRAME_WIDTH = 300
FRAME_PADDING = 25
TEXT_PADDING = 10
SYMBOL_WIDTH = 20
SYMBOL_PADDING = 2.5

TITLE_SIZE = 16
TEXT_SIZE = 12

FONT_BOLD_ENG = "Helvetica-Bold"
FONT_BOLD_JPN = "NotoSansJP-Bold"

FONT_ENG = "Helvetica"
FONT_JPN = "NotoSansJP"

V_ALIGN_TOP = "top"
V_ALIGN_MIDDLE = "middle"
V_ALIGN_BOTTOM = "bottom"

H_ALIGN_LEFT = "left"
H_ALIGN_CENTRE = "centre"
H_ALIGN_RIGHT = "right"


def generate_pdf(series, img_folder_path, output_path):
    page_size = A4
    page_width, page_height = page_size

    # Create a new PDF document
    c = canvas.Canvas(output_path, pagesize=A4)
        
    frame_image_path = os.path.join(img_folder_path, FRAME_FILENAME)
    frame_image = Image.open(frame_image_path)
    frame_image_io = get_image_io(frame_image)

    frame_width, frame_height = frame_image.size
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
        serie_name = serie['name']

        # DEBUG
        # if serie_name not in ["Scarlet & Violet"]:
        #     continue

        print(f"\n{serie_name}")

        sets = serie["sets"]
        for set in sets:
            page = page + 1
            set_name = set['name']

            # DEBUG
            # if page != 45:
            #     continue
            # if set_name not in ["SVP Black Star Promos"]:
            #     continue

            print(f"  {page}. {set_name}")

            # Set the background image for the current page
            if "cover" in set:
                cover_image_filename = set["cover"]
                cover_image_path = os.path.join(img_folder_path, cover_image_filename)
                cropped_img = crop_image_to_cover(cover_image_path, page_size)
                cropped_img_io = get_image_io(cropped_img)
                c.drawImage(cropped_img_io, 0, 0, width=page_width, height=page_height)

            # Draw the frame
            c.drawImage(frame_image_io, frame_x, frame_y, width=frame_width, height=frame_height, mask='auto', preserveAspectRatio=True)
            
            # Write the title (and subtitle if present)
            title_font = FONT_BOLD_ENG
            title_y = frame_centre_y
            if "name-en" in set:
                title_font = FONT_BOLD_JPN
                title_y = frame_centre_y + TEXT_SIZE/2
                subtitle_y = frame_centre_y - TITLE_SIZE/2
                write_text(set["name-en"], frame_centre_x, subtitle_y, c, h_align=H_ALIGN_CENTRE, v_align=V_ALIGN_MIDDLE)
            write_text(set_name, frame_centre_x, title_y, c, title_font, TITLE_SIZE, H_ALIGN_CENTRE, V_ALIGN_MIDDLE)

            # Write the series name in the top-left corner
            write_text(serie_name, padded_frame_left_x, padded_frame_top_y, c, h_align=H_ALIGN_LEFT, v_align=V_ALIGN_TOP)

            # Draw the symbol(s)
            if "symbols" in set:
                symbol_x = padded_frame_left_x
                for symbol in set["symbols"]:
                    draw_symbol(symbol, symbol_x, padded_frame_bottom_y, c)
                    symbol_x = symbol_x + get_symbol_width(symbol) + SYMBOL_PADDING

            # Write the date in the bottom-right corner
            if "date" in set:
                write_text(set['date'], frame_right_x - TEXT_PADDING, frame_bottom_y + TEXT_PADDING, c, h_align=H_ALIGN_RIGHT, v_align=V_ALIGN_BOTTOM)

            # Add a new page
            c.showPage()

    # Save and close the PDF document
    c.save()


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


def draw_symbol(symbol, x, y, canvas):
    symbol_path = os.path.join(img_folder_path, symbol)
    symbol_image = Image.open(symbol_path)
    symbol_image_io = get_image_io(symbol_image)
    symbol_width, symbol_height = symbol_image.size
    symbol_ratio = symbol_width / symbol_height
    symbol_width, symbol_height = (SYMBOL_WIDTH, SYMBOL_WIDTH / symbol_ratio)
    canvas.drawImage(symbol_image_io, x, y, width=symbol_width, height=symbol_height, mask='auto')


def get_symbol_width(symbol):
    symbol_path = os.path.join(img_folder_path, symbol)
    symbol_image = Image.open(symbol_path)
    symbol_width, symbol_height = symbol_image.size
    symbol_ratio = symbol_width / symbol_height
    symbol_width, symbol_height = (SYMBOL_WIDTH, SYMBOL_WIDTH / symbol_ratio)
    return symbol_width


def str_to_bool(v):
  return v.lower() in ("yes", "true", "t", "1")


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
img_folder_path = os.path.join(script_directory, IMG_FOLDER_PATH)
fonts_folder_path = os.path.join(script_directory, FONTS_FOLDER_PATH)

# Register Japanese fonts
jp_title_font_path = os.path.join(fonts_folder_path, "NotoSansJP-Bold.ttf")
pdfmetrics.registerFont(TTFont(FONT_BOLD_JPN, jp_title_font_path))
jp_text_font_path = os.path.join(fonts_folder_path, "NotoSansJP-Regular.ttf")
pdfmetrics.registerFont(TTFont(FONT_JPN, jp_text_font_path))

# Parse the catalog data from the JSON file to a dictionary
catalog = read_catalog_from_json(json_file_path)

# Generate the PDF
generate_pdf(catalog, img_folder_path, output_file_path)
