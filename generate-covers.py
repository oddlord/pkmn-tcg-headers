import os
from argparse import ArgumentParser
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from PIL import Image

import scripts.utils as u

# Links:
# https://bulbapedia.bulbagarden.net/wiki/List_of_Pok%C3%A9mon_Trading_Card_Game_expansions
# https://bulbapedia.bulbagarden.net/wiki/List_of_Japanese_Pok%C3%A9mon_Trading_Card_Game_expansions

CATALOG_DIR_PATH = "assets/catalog"
IMGS_DIR_PATH = "assets/imgs"
FRAME_IMGS_DIR_PATH = "assets/imgs/frame"
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

LOG_INDENT = "  "

FRAME_BORDER_THICKNESS = 10
FRAME_WIDTH = 300
FRAME_HEIGHT = 100
FRAME_MARGIN = 25
FRAME_PADDING = 2
FRAME_MIN_TITLE_PADDING = 10

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
    c = canvas.Canvas(output_path, pagesize=page_size)

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
                set_name_alt_width = u.get_text_width(set_name_alt, font_size=TEXT_SIZE)

            frame_width = max(FRAME_WIDTH, set_name_width + 2*FRAME_MIN_TITLE_PADDING, set_name_alt_width + 2*FRAME_MIN_TITLE_PADDING)

            frame_right_x = page_width - FRAME_MARGIN
            frame_left_x = frame_right_x - frame_width - 2*FRAME_BORDER_THICKNESS
            frame_top_y = page_height - FRAME_MARGIN
            frame_bottom_y = frame_top_y - FRAME_HEIGHT - 2*FRAME_BORDER_THICKNESS

            frame_padding = FRAME_PADDING
            padded_frame_left_x = frame_left_x + FRAME_BORDER_THICKNESS + frame_padding
            padded_frame_top_y = frame_top_y - FRAME_BORDER_THICKNESS - frame_padding
            padded_frame_right_x = frame_right_x - FRAME_BORDER_THICKNESS - frame_padding
            padded_frame_bottom_y = frame_bottom_y + FRAME_BORDER_THICKNESS + frame_padding

            frame_centre_x = frame_left_x + (frame_right_x - frame_left_x)/2
            frame_centre_y = frame_bottom_y + (frame_top_y - frame_bottom_y)/2

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
            set_print_str = f"{LOG_INDENT}{page}. {set_print_name}"
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
                cropped_img = u.crop_image_to_cover(set_cover_path, page_size)
                cropped_img_io = u.get_image_io(cropped_img)
                c.drawImage(cropped_img_io, 0, 0, width=page_width, height=page_height)

            # Draw the frame
            # c.drawImage(frame_img_io, frame_x, frame_y, width=frame_width, height=frame_height, mask='auto', preserveAspectRatio=True)
            u.draw_frame(frame_right_x, frame_top_y, c, width=frame_width, height=FRAME_HEIGHT, border_thickness=FRAME_BORDER_THICKNESS, h_align=u.H_ALIGN_RIGHT, v_align=u.V_ALIGN_TOP)

            # Write the set's name and alternative name, if present
            title_y = frame_centre_y
            subtitle_y = frame_centre_y
            if set_name and set_name_alt:
                title_y = frame_centre_y + TEXT_SIZE/2
                subtitle_y = frame_centre_y - TITLE_SIZE/2
            if set_name:
                u.write_text(set_name, frame_centre_x, title_y, c, font_weight=u.FONT_WEIGHT_BOLD, font_size=TITLE_SIZE, h_align=u.H_ALIGN_CENTRE, v_align=u.V_ALIGN_MIDDLE)
            if set_name_alt:
                u.write_text(set_name_alt, frame_centre_x, subtitle_y, c, font_size=TEXT_SIZE, h_align=u.H_ALIGN_CENTRE, v_align=u.V_ALIGN_MIDDLE)

            # Write the serie name in the top-left corner, if present
            if serie_name:
                u.write_text(serie_name, padded_frame_left_x, padded_frame_top_y, c, font_size=TEXT_SIZE, h_align=u.H_ALIGN_LEFT, v_align=u.V_ALIGN_TOP)

            # Write the date in the bottom-right corner, if present
            if DATE_KEY in set:
                set_date = set[DATE_KEY]
                u.write_text(set_date, padded_frame_right_x, padded_frame_bottom_y, c, font_size=TEXT_SIZE, h_align=u.H_ALIGN_RIGHT, v_align=u.V_ALIGN_BOTTOM)

            # Draw the symbol(s), if present
            symbol_x = padded_frame_left_x
            for symbol_path in set_symbol_paths:
                u.draw_image(symbol_path, symbol_x, padded_frame_bottom_y, c, width=SYMBOL_WIDTH)
                symbol_x = symbol_x + SYMBOL_WIDTH + SYMBOL_PADDING

            # Draw the region symbol, if specified
            if REGION_KEY in set:
                set_region = set[REGION_KEY]
                if set_region in REGION_FILENAMES:
                    region_filename = REGION_FILENAMES[set_region]
                    region_path = os.path.join(img_dir_path, region_filename)
                    u.draw_image(region_path, padded_frame_right_x, padded_frame_top_y, c, width=SYMBOL_WIDTH, h_align=u.H_ALIGN_RIGHT, v_align=u.V_ALIGN_TOP)

            # Render the page
            c.showPage()

    print("")

    # Save and close the PDF document
    c.save()


# Get the directory path of the script
script_directory = os.path.dirname(os.path.abspath(__file__))

# Get paths
json_file_path = os.path.join(script_directory, CATALOG_FILENAME)
output_file_path = os.path.join(script_directory, OUTPUT_FILENAME)
img_dir_path = os.path.join(script_directory, IMGS_DIR_PATH)
frame_imgs_dir_path = os.path.join(script_directory, FRAME_IMGS_DIR_PATH)
catalog_dir_path = os.path.join(script_directory, CATALOG_DIR_PATH)
fonts_dir_path = os.path.join(script_directory, FONTS_DIR_PATH)

# Init the utils module
u.init(fonts_dir_path, frame_imgs_dir_path)

# Parse command line arguments
parser = ArgumentParser()
parser.add_argument(
    "-f", "--filter",
    help="Specify a filter json file",
    dest="filter_filename",
    default=None,
    metavar="FILE")
args = parser.parse_args()

# Parse the filter JSON file
filter = None
if args.filter_filename:
    filter_file_path = os.path.join(script_directory, args.filter_filename)
    filter = u.parse_json(filter_file_path)

# Parse the catalog data from the catalog JSON file
catalog = u.parse_json(json_file_path)

# Generate the PDF
generate_pdf(catalog, img_dir_path, catalog_dir_path, output_file_path, filter=filter)
