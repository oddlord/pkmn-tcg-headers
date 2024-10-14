import os
import json
from argparse import ArgumentParser
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from PIL import Image

import scripts.utils as u

# Links:
# https://bulbapedia.bulbagarden.net/wiki/List_of_Pok%C3%A9mon_Trading_Card_Game_expansions
# https://bulbapedia.bulbagarden.net/wiki/List_of_Japanese_Pok%C3%A9mon_Trading_Card_Game_expansions

# TODO
# Make frame modular (corners/sides) and make it scale based on its content

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

TITLE_SIZE = 16
TEXT_SIZE = 12

SYMBOL_WIDTH = 20
SYMBOL_PADDING = 2.5

ID_KEY = "id"
NAME_KEY = "name"
SETS_KEY = "sets"
DATE_KEY = "date"
REGION_KEY = "region"
NAME_ALT_KEY = "name_alt"


def generate_pdf(series, img_dir_path, catalog_dir_path, output_path, filter=None):
    page_size = A4
    page_width, page_height = page_size

    # Create a new PDF document
    c = canvas.Canvas(output_path, pagesize=A4)
        
    frame_img_path = os.path.join(img_dir_path, FRAME_FILENAME)
    frame_img = Image.open(frame_img_path)
    frame_img_io = u.get_image_io(frame_img)

    page = 0
    for serie in series:
        if ID_KEY not in serie:
            continue

        serie_id = serie[ID_KEY]
        serie_dir_path = os.path.join(catalog_dir_path, serie_id)

        serie_name = None
        if NAME_KEY in serie:
            serie_name = serie[NAME_KEY]

        serie_print_name = serie_name or f"<{serie_id}>"
        has_printed_serie = False

        sets = []
        if SETS_KEY in serie:
            sets = serie[SETS_KEY]

        for set in sets:
            if ID_KEY not in set:
                continue

            set_id = set[ID_KEY]
            set_dir_path = os.path.join(serie_dir_path, set_id)

            set_name = None
            set_name_width = 0
            if NAME_KEY in set:
                set_name = set[NAME_KEY]
                set_name_width = u.get_text_width(set_name, font_weight=u.FONT_WEIGHT_BOLD, font_size=TITLE_SIZE)

            set_name_alt = None
            set_name_alt_width = 0
            if NAME_ALT_KEY in set:
                set_name_alt = set[NAME_ALT_KEY]
                set_name_alt_width = u.get_text_width(set_name_alt)

            frame_width, frame_height = frame_img.size
            frame_ratio = frame_width / frame_height
            frame_width = max(FRAME_WIDTH, set_name_width + 2*FRAME_PADDING, set_name_alt_width + 2*FRAME_PADDING)
            frame_height = frame_width / frame_ratio
            frame_x, frame_y = (page_width - frame_width - FRAME_PADDING, page_height - frame_height - FRAME_PADDING)

            frame_left_x = frame_x
            frame_top_y = frame_y + frame_height
            frame_right_x = frame_x + frame_width
            frame_bottom_y = frame_y

            text_padding = TEXT_PADDING * (frame_width / FRAME_WIDTH)
            padded_frame_left_x = frame_left_x + text_padding
            padded_frame_top_y = frame_top_y - text_padding
            padded_frame_right_x = frame_right_x - text_padding
            padded_frame_bottom_y = frame_bottom_y + text_padding

            frame_centre_x = frame_left_x + frame_width/2
            frame_centre_y = frame_bottom_y + frame_height/2

            if set_name:
                set_print_name = set_name
                if set_name_alt:
                    set_print_name += f" ({set_name_alt})"
            elif set_name_alt:
                set_print_name = set_name_alt
            else:
                set_print_name = f"<{set_id}>"

            if filter and serie_id not in filter["allowed_series"] and f"{serie_id}/{set_id}" not in filter["allowed_sets"]:
                continue

            page = page + 1
            set_print_str = f"{SET_LOG_INDENT}{page}. {set_print_name}"
            if not has_printed_serie:
                print(f"\n{serie_print_name}")
                has_printed_serie = True
            print(set_print_str)

            set_cover_path = None
            set_symbol_paths = []
            if os.path.isdir(set_dir_path):
                set_files = os.listdir(set_dir_path)
                for file in set_files:
                    if file.startswith(f"{COVER_FILENAME_PREFIX}."):
                        set_cover_path = os.path.join(set_dir_path, file)
                    if file.startswith(f"{SYMBOL_FILENAME_PREFIX}"):
                        symbol_path = os.path.join(set_dir_path, file)
                        set_symbol_paths.append(symbol_path)

            # Draw the cover, if present
            if set_cover_path:
                cropped_img = crop_image_to_cover(set_cover_path, page_size)
                cropped_img_io = u.get_image_io(cropped_img)
                c.drawImage(cropped_img_io, 0, 0, width=page_width, height=page_height)

            # Draw the frame
            c.drawImage(frame_img_io, frame_x, frame_y, width=frame_width, height=frame_height, mask='auto', preserveAspectRatio=True)

            # Write the set's name and alternative name, if present
            title_y = frame_centre_y
            subtitle_y = frame_centre_y
            if set_name and set_name_alt:
                title_y = frame_centre_y + TEXT_SIZE/2
                subtitle_y = frame_centre_y - TITLE_SIZE/2
            if set_name:
                u.write_text(set_name, frame_centre_x, title_y, c, font_weight=u.FONT_WEIGHT_BOLD, font_size=TITLE_SIZE, h_align=u.H_ALIGN_CENTRE, v_align=u.V_ALIGN_MIDDLE)
            if set_name_alt:
                u.write_text(set_name_alt, frame_centre_x, subtitle_y, c, h_align=u.H_ALIGN_CENTRE, v_align=u.V_ALIGN_MIDDLE)

            # Write the serie name in the top-left corner, if present
            if serie_name:
                u.write_text(serie_name, padded_frame_left_x, padded_frame_top_y, c, h_align=u.H_ALIGN_LEFT, v_align=u.V_ALIGN_TOP)

            # Write the date in the bottom-right corner, if present
            if DATE_KEY in set:
                set_date = set[DATE_KEY]
                u.write_text(set_date, padded_frame_right_x, padded_frame_bottom_y, c, h_align=u.H_ALIGN_RIGHT, v_align=u.V_ALIGN_BOTTOM)

            # Draw the symbol(s), if present
            symbol_x = padded_frame_left_x
            for symbol_path in set_symbol_paths:
                u.draw_symbol(symbol_path, symbol_x, padded_frame_bottom_y, c)
                symbol_x = symbol_x + SYMBOL_WIDTH + SYMBOL_PADDING

            # Draw the region symbol, if specified
            if REGION_KEY in set:
                set_region = set[REGION_KEY]
                if set_region in REGION_FILENAMES:
                    region_filename = REGION_FILENAMES[set_region]
                    region_path = os.path.join(IMGS_DIR_PATH, region_filename)
                    u.draw_symbol(region_path, padded_frame_right_x, padded_frame_top_y, c, h_align=u.H_ALIGN_RIGHT, v_align=u.V_ALIGN_TOP)

            # Render the page
            c.showPage()

    print("")

    # Save and close the PDF document
    c.save()


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


def parse_json(file_path):
    with open(file_path, encoding='utf-8') as f:
        txt = f.read()
        parsed = json.loads(txt)
    return parsed


# Get the directory path of the script
script_directory = os.path.dirname(os.path.abspath(__file__))

# Init the utils module
u.init(script_directory, FONTS_DIR_PATH, TEXT_SIZE, SYMBOL_WIDTH)

# Parse command line arguments
parser = ArgumentParser()
parser.add_argument(
    "-f", "--filter",
    help="Specify a filter json file",
    dest="filter_filename",
    default=None,
    metavar="FILE")
args = parser.parse_args()

# Get paths
json_file_path = os.path.join(script_directory, CATALOG_FILENAME)
output_file_path = os.path.join(script_directory, OUTPUT_FILENAME)
img_dir_path = os.path.join(script_directory, IMGS_DIR_PATH)
catalog_dir_path = os.path.join(script_directory, CATALOG_DIR_PATH)

# Parse the filter JSON file
filter = None
if args.filter_filename:
    filter_file_path = os.path.join(script_directory, args.filter_filename)
    filter = parse_json(filter_file_path)

# Parse the catalog data from the catalog JSON file
catalog = parse_json(json_file_path)

# Generate the PDF
generate_pdf(catalog, img_dir_path, catalog_dir_path, output_file_path, filter=filter)
