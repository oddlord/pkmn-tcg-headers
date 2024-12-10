import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

import scripts.utils as u

FRAME_BORDER_THICKNESS = 7.5
FRAME_PADDING = 1.5
FRAME_MIN_INTERNAL_ELEMENTS_SPACING = 5

TITLE_SIZE = 24
TEXT_SIZE = 12
NAMES_PADDING = 5

NAME_FONT_WEIGHT = u.FONT_WEIGHT_BOLD
NAME_ALT_FONT_WEIGHT = u.FONT_WEIGHT_REGULAR

SYMBOL_WIDTH = 14
SYMBOL_PADDING = 1.5

class CardGenerator():
    def __init__(self, config):
        self.config = config
    
    def generate(self):
        page_size = A4
        page_width, page_height = page_size

        card_size = (63.5*mm, 88*mm)
        card_width, card_height = card_size

        card_spacing_h = (page_width - 3*card_width)/4
        card_spacing_v = (page_height - 3*card_height)/4

        frame_full_width = card_width
        frame_full_height = card_height/2
        name_max_width = frame_full_width - 2*FRAME_MIN_INTERNAL_ELEMENTS_SPACING - 2*FRAME_BORDER_THICKNESS

        # Create a new PDF document
        c = canvas.Canvas(self.config.output_file_path, pagesize=page_size)

        card = 0
        for serie in self.config.catalog:
            if "id" not in serie:
                continue

            serie_id = serie["id"]
            serie_dir_path = os.path.join(self.config.catalog_assets_dir_path, serie_id)

            serie_name = None
            serie_name_width = 0
            if "name" in serie:
                serie_name = serie["name"]
                serie_name_width = u.get_text_width(serie_name, font_size=TEXT_SIZE)

            serie_print_name = serie_name or f"<{serie_id}>"
            has_printed_serie = False

            sets = []
            if "sets" in serie:
                sets = serie["sets"]

            for set in sets:
                if "id" not in set:
                    continue

                set_id = set["id"]

                # Check if this set should be skipped
                if self.config.filtered_sets and serie_id not in self.config.filtered_sets["allowed_series"] and f"{serie_id}/{set_id}" not in self.config.filtered_sets["allowed_sets"]:
                    continue

                card = card + 1
                page = (card-1)//9 +1
                card_in_page = (card-1)%9 +1
                set_dir_path = os.path.join(serie_dir_path, set_id)

                # Get the set name, if present
                set_name = None
                set_name_font_size = TITLE_SIZE
                if "name" in set:
                    set_name = set["name"]
                    while True:
                        set_name_width = u.get_text_width(set_name, font_weight=NAME_FONT_WEIGHT, font_size=set_name_font_size)
                        if set_name_width <= name_max_width:
                            break
                        set_name_font_size = set_name_font_size - 1

                # Get the set alt name, if present
                set_name_alt = None
                set_name_alt_font_size = TEXT_SIZE
                if "name_alt" in set:
                    set_name_alt = set["name_alt"]
                    while True:
                        set_name_alt_width = u.get_text_width(set_name_alt, font_weight=NAME_ALT_FONT_WEIGHT, font_size=set_name_alt_font_size)
                        if set_name_alt_width <= name_max_width:
                            break
                        set_name_alt_font_size = set_name_alt_font_size - 1

                # Build the set print name
                if set_name:
                    set_print_name = set_name
                    if set_name_alt:
                        set_print_name += f" ({set_name_alt})"
                elif set_name_alt:
                    set_print_name = set_name_alt
                else:
                    set_print_name = f"<{set_id}>"

                # Print the set to console
                set_print_str = f"{page}.{card_in_page}. {set_print_name}"
                if not has_printed_serie:
                    u.log(f"\n{serie_print_name}")
                    has_printed_serie = True
                u.log(set_print_str, 1)

                # Get the set region symbol, if specified
                region_filename = None
                if "region" in set:
                    set_region = set["region"]
                    if set_region in self.config.region_filenames:
                        region_filename = self.config.region_filenames[set_region]

                # Get the set date, if present
                set_date = None
                if "date" in set:
                    set_date = set["date"]

                # Search for the cover and symbol(s)
                set_cover_path = None
                set_symbol_paths = []
                if os.path.isdir(set_dir_path):
                    set_files = os.listdir(set_dir_path)
                    for file in set_files:
                        if file.startswith(self.config.cover_filename_prefix):
                            set_cover_path = os.path.join(set_dir_path, file)
                        if file.startswith(self.config.symbol_filename_prefix):
                            symbol_path = os.path.join(set_dir_path, file)
                            set_symbol_paths.append(symbol_path)

                card_col = (card_in_page-1)%3
                card_row = (card_in_page-1)//3

                card_x = card_col*card_width + (card_col+1)*card_spacing_h
                card_y = page_height - (card_row*card_height + (card_row+1)*card_spacing_v)

                # Calculate frame values
                frame_left_x = card_x
                frame_right_x = frame_left_x + frame_full_width
                frame_bottom_y = card_y - card_height
                frame_top_y = frame_bottom_y + frame_full_height

                padded_frame_left_x = frame_left_x + FRAME_BORDER_THICKNESS + FRAME_PADDING
                padded_frame_top_y = frame_top_y - FRAME_BORDER_THICKNESS - FRAME_PADDING
                padded_frame_right_x = frame_right_x - FRAME_BORDER_THICKNESS - FRAME_PADDING
                padded_frame_bottom_y = frame_bottom_y + FRAME_BORDER_THICKNESS + FRAME_PADDING

                frame_centre_x = frame_left_x + (frame_right_x - frame_left_x)/2
                frame_centre_y = frame_bottom_y + (frame_top_y - frame_bottom_y)/2
                # Calculate frame values --- END

                # Draw the cover, if present
                if set_cover_path:
                    u.draw_image(set_cover_path, card_x, card_y, c, width=card_width, height=card_height, crop_to_cover=True, h_align=u.H_ALIGN_LEFT, v_align=u.V_ALIGN_TOP, border_width=3)

                # Draw the frame
                u.draw_frame(frame_left_x, frame_bottom_y, c, width=frame_full_width, height=frame_full_height, border_thickness=FRAME_BORDER_THICKNESS, h_align=u.H_ALIGN_LEFT, v_align=u.V_ALIGN_BOTTOM, is_full_size=True)

                # Write the set's name and alternative name, if present
                title_y = frame_centre_y
                subtitle_y = frame_centre_y
                if set_name and set_name_alt:
                    names_padding = NAMES_PADDING * (set_name_font_size/TITLE_SIZE)
                    title_y = frame_centre_y + (set_name_font_size+names_padding+set_name_alt_font_size)/2 - set_name_font_size/2
                    subtitle_y = frame_centre_y - (set_name_font_size+names_padding+set_name_alt_font_size)/2 + set_name_alt_font_size/2
                if set_name:
                    u.write_text(set_name, frame_centre_x, title_y, c, font_weight=NAME_FONT_WEIGHT, font_size=set_name_font_size, h_align=u.H_ALIGN_CENTRE, v_align=u.V_ALIGN_MIDDLE)
                if set_name_alt:
                    u.write_text(set_name_alt, frame_centre_x, subtitle_y, c, font_weight=NAME_ALT_FONT_WEIGHT, font_size=set_name_alt_font_size, h_align=u.H_ALIGN_CENTRE, v_align=u.V_ALIGN_MIDDLE)

                # Write the serie name in the top-left corner, if present
                if serie_name:
                    u.write_text(serie_name, padded_frame_left_x, padded_frame_top_y, c, font_size=TEXT_SIZE, h_align=u.H_ALIGN_LEFT, v_align=u.V_ALIGN_TOP)

                # Write the date in the bottom-right corner, if present
                if set_date:
                    u.write_text(set_date, padded_frame_right_x, padded_frame_bottom_y, c, font_size=TEXT_SIZE, h_align=u.H_ALIGN_RIGHT, v_align=u.V_ALIGN_BOTTOM)

                # Draw the symbol(s), if present
                symbol_x = padded_frame_left_x
                for symbol_path in set_symbol_paths:
                    symbol_w, _ = u.draw_image(symbol_path, symbol_x, padded_frame_bottom_y, c, width=SYMBOL_WIDTH)
                    symbol_x = symbol_x + symbol_w + SYMBOL_PADDING

                # Draw the region symbol, if specified
                if region_filename:
                    region_path = os.path.join(self.config.imgs_dir_path, region_filename)
                    u.draw_image(region_path, padded_frame_right_x, padded_frame_top_y, c, width=SYMBOL_WIDTH, h_align=u.H_ALIGN_RIGHT, v_align=u.V_ALIGN_TOP, border_width=1)

                if (card_in_page == 9):
                    # Render the page
                    c.showPage()

        if (card_in_page < 9):
            # Render the page
            c.showPage()

        u.log("")

        # Save and close the PDF document
        c.save()
