import io
import os
import json
import sys
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth
from PIL import Image

# Links:
# https://bulbapedia.bulbagarden.net/wiki/List_of_Pok%C3%A9mon_Trading_Card_Game_expansions
# https://bulbapedia.bulbagarden.net/wiki/List_of_Japanese_Pok%C3%A9mon_Trading_Card_Game_expansions

OUTPUT_FILENAME = "covers.pdf"
CATALOG_FILENAME = "catalog.json"
IMG_FOLDER_PATH = "assets/img"
FRAME_FILENAME = "frame.png"
JPN_SYMBOL_FILENAME = "jpn.jpg"

FRAME_WIDTH = 300
FRAME_PADDING = 25
TEXT_PADDING = 10
SYMBOL_WIDTH = 20
SYMBOL_PADDING = 2.5
JPN_SYMBOL_WIDTH = 20
TITLE_SIZE = 16
TEXT_SIZE = 12


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

    jpn_symbol_path = os.path.join(img_folder_path, JPN_SYMBOL_FILENAME)
    jpn_symbol_image = Image.open(jpn_symbol_path)
    jpn_symbol_width, jpn_symbol_height = jpn_symbol_image.size
    jpn_symbol_ratio = jpn_symbol_width / jpn_symbol_height
    jpn_symbol_width, jpn_symbol_height = (JPN_SYMBOL_WIDTH, JPN_SYMBOL_WIDTH / jpn_symbol_ratio)
    jpn_symbol_x, jpn_symbol_y = (frame_right_x - jpn_symbol_width - TEXT_PADDING, frame_top_y - jpn_symbol_height - TEXT_PADDING)

    page = 0
    for serie in series:
        serie_name = serie['name']
        print(f"\n{serie_name}")
        sets = serie["sets"]
        for set in sets:
            page = page + 1
            set_name = set['name']

            # DEBUG
            # if page != 6:
            #     continue
            # if set_name not in ["Supreme Victors"]:
            #     continue

            print(f"  {page}. {set_name}")

            # Set the background image for the current page
            if "cover" in set:
                cover_image_filename = set["cover"]
                cover_image_path = os.path.join(img_folder_path, cover_image_filename)
                cropped_img = crop_image_to_cover(cover_image_path, page_size)
                cropped_img_io = get_image_io(cropped_img)
                c.drawImage(cropped_img_io, 0, 0, width=page_width, height=page_height)

            c.drawImage(frame_image_io, frame_x, frame_y, width=frame_width, height=frame_height, mask='auto', preserveAspectRatio=True)
            
            font_name = "Helvetica-Bold"
            font_size = TITLE_SIZE
            c.setFont(font_name, font_size)
            text = set_name
            text_width = stringWidth(text, font_name, font_size)
            text_x, text_y = (frame_left_x + (frame_width - text_width) / 2, frame_bottom_y + (frame_height - font_size) / 2)
            c.drawString(text_x, text_y, text)

            font_name = "Helvetica"
            font_size = TEXT_SIZE
            c.setFont(font_name, font_size)
            text = serie_name
            text_width = stringWidth(text, font_name, font_size)
            text_x, text_y = (frame_left_x + TEXT_PADDING, frame_top_y - font_size - TEXT_PADDING)
            c.drawString(text_x, text_y, text)

            if "is-special-expansion" in set:
                is_subset = str2bool(set['is-special-expansion'])
                if is_subset:
                    text = "(special expansion)"
                    text_width = stringWidth(text, font_name, font_size)
                    text_x, text_y = (frame_left_x + TEXT_PADDING, frame_top_y - font_size - TEXT_PADDING - TEXT_SIZE)
                    c.drawString(text_x, text_y, text)

            if "symbols" in set:
                symbol_x = frame_left_x + TEXT_PADDING
                for symbol in set["symbols"]:
                    symbol_path = os.path.join(img_folder_path, symbol)
                    symbol_image = Image.open(symbol_path)
                    symbol_image_io = get_image_io(symbol_image)
                    symbol_width, symbol_height = symbol_image.size
                    symbol_ratio = symbol_width / symbol_height
                    symbol_width, symbol_height = (SYMBOL_WIDTH, SYMBOL_WIDTH / symbol_ratio)
                    symbol_y = frame_bottom_y + TEXT_PADDING
                    c.drawImage(symbol_image_io, symbol_x, symbol_y, width=symbol_width, height=symbol_height, mask='auto')

                    symbol_x = symbol_x + symbol_width + SYMBOL_PADDING

            if "is-jpn-only" in set:
                is_jpn_only = str2bool(set["is-jpn-only"])
                if is_jpn_only:
                    c.drawImage(jpn_symbol_path, jpn_symbol_x, jpn_symbol_y, width=jpn_symbol_width, height=jpn_symbol_height, mask='auto')

            if "date" in set:
                font_name = "Helvetica"
                font_size = TEXT_SIZE
                c.setFont(font_name, font_size)
                text = set['date']
                text_width = stringWidth(text, font_name, font_size)
                text_x, text_y = (frame_right_x - TEXT_PADDING - text_width, frame_bottom_y + TEXT_PADDING)
                c.drawString(text_x, text_y, text)

            # Add a new page
            c.showPage()

    # Save and close the PDF document
    c.save()


def str2bool(v):
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
        # The image is wider, crop horizontally
        new_image_width = int(image_height * page_ratio)
        left = (image_width - new_image_width) // 2
        right = left + new_image_width
        top, bottom = 0, image_height
    else:
        # The image is taller, crop vertically
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


# Read the page data from a JSON file
def read_catalog_from_json(file_path):
    with open(file_path, encoding='utf-8') as f:
        txt = f.read()
        catalog = json.loads(txt)
    return catalog


# Get the directory path of the script
script_directory = os.path.dirname(os.path.abspath(__file__))

json_file_path = os.path.join(script_directory, CATALOG_FILENAME)
output_file_path = os.path.join(script_directory, OUTPUT_FILENAME)
img_folder_path = os.path.join(script_directory, IMG_FOLDER_PATH)

# Read the page data from the JSON file
catalog = read_catalog_from_json(json_file_path)

# Generate the PDF
generate_pdf(catalog, img_folder_path, output_file_path)