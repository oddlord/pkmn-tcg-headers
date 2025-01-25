import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

import scripts.utils as u

FRAME_BORDER_THICKNESS = 10
FRAME_MIN_WIDTH = 200
FRAME_HEIGHT = 100
FRAME_MARGIN = 25
FRAME_PADDING = 2
FRAME_MIN_INTERNAL_ELEMENTS_SPACING = 15

TITLE_SIZE = 16
TEXT_SIZE = 12

SYMBOL_WIDTH = 20
SYMBOL_PADDING = 2.5

class PageGenerator():    
    def generate(self, data):
        page_size = A4
        page_width, page_height = page_size

        # Create a new PDF document
        c = canvas.Canvas(data.output_file_path, pagesize=page_size)

        page = 0
        for serie in data.catalog:
            if "id" not in serie:
                continue

            serie_id = serie["id"]
            serie_dir_path = os.path.join(data.catalog_assets_dir_path, serie_id)

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

                # Check whether this set is included or not
                if not u.is_set_included(serie_id, set_id, data.config["filters"]):
                    continue

                page = page + 1
                set_dir_path = os.path.join(serie_dir_path, set_id)

                # Get the set region symbol, if specified
                set_region = "eng"  # Defaults to English
                region_filename = None
                region_symbol_width = 0
                if "region" in set:
                    set_region = set["region"]
                    if set_region in data.region_filenames:
                        region_filename = data.region_filenames[set_region]
                        region_symbol_width = SYMBOL_WIDTH

                set_names_dict = {}
                if "names" in set:
                    set_names_dict = set["names"]

                # Get the set name, if present
                set_name = None
                set_name_width = 0
                if set_region in set_names_dict:
                    set_name = set_names_dict[set_region]
                    set_name_separator = "" if u.text_contains_asian_chars(set_name) else " "
                    set_name = set_name.replace("\n", set_name_separator)
                    set_name_width = u.get_text_width(set_name, font_weight=u.FONT_WEIGHT_BOLD, font_size=TITLE_SIZE)

                # Get the set alt name, if present
                set_name_alt = None
                set_name_alt_width = 0
                if set_region != "eng" and "eng" in set_names_dict:
                    set_name_alt = set_names_dict["eng"]
                    set_name_alt_width = u.get_text_width(set_name_alt, font_size=TEXT_SIZE)

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
                set_print_str = f"{page}. {set_print_name}"
                if not has_printed_serie:
                    u.log(f"\n{serie_print_name}")
                    has_printed_serie = True
                u.log(set_print_str, 1)

                # Get the set date, if present
                set_date = None
                set_date_width = 0
                if "date" in set:
                    set_date = set["date"]
                    set_date_width = u.get_text_width(set_date, font_size=TEXT_SIZE)

                # Search for the cover and symbol(s)
                set_cover_path = None
                set_symbol_paths = []
                if os.path.isdir(set_dir_path):
                    set_files = os.listdir(set_dir_path)
                    for file in set_files:
                        if file.startswith(data.cover_filename_prefix):
                            set_cover_path = os.path.join(set_dir_path, file)
                        if file.startswith(data.symbol_filename_prefix):
                            symbol_path = os.path.join(set_dir_path, file)
                            set_symbol_paths.append(symbol_path)
                set_symbols_tot_width = len(set_symbol_paths)*SYMBOL_WIDTH + max(0, len(set_symbol_paths)-1)*SYMBOL_PADDING
                
                # Calculate frame values
                frame_width = max(
                    FRAME_MIN_WIDTH,
                    set_name_width + 2*FRAME_MIN_INTERNAL_ELEMENTS_SPACING,
                    set_name_alt_width + 2*FRAME_MIN_INTERNAL_ELEMENTS_SPACING,
                    serie_name_width + FRAME_MIN_INTERNAL_ELEMENTS_SPACING + region_symbol_width,
                    set_symbols_tot_width + FRAME_MIN_INTERNAL_ELEMENTS_SPACING + set_date_width)
                frame_height = FRAME_HEIGHT

                frame_right_x = page_width - FRAME_MARGIN
                frame_left_x = frame_right_x - frame_width - 2*FRAME_BORDER_THICKNESS
                frame_top_y = page_height - FRAME_MARGIN
                frame_bottom_y = frame_top_y - frame_height - 2*FRAME_BORDER_THICKNESS

                padded_frame_left_x = frame_left_x + FRAME_BORDER_THICKNESS + FRAME_PADDING
                padded_frame_top_y = frame_top_y - FRAME_BORDER_THICKNESS - FRAME_PADDING
                padded_frame_right_x = frame_right_x - FRAME_BORDER_THICKNESS - FRAME_PADDING
                padded_frame_bottom_y = frame_bottom_y + FRAME_BORDER_THICKNESS + FRAME_PADDING

                frame_centre_x = frame_left_x + (frame_right_x - frame_left_x)/2
                frame_centre_y = frame_bottom_y + (frame_top_y - frame_bottom_y)/2
                # Calculate frame values --- END

                # Draw the cover, if present
                if set_cover_path:
                    u.draw_image(set_cover_path, 0, 0, c, width=page_width, height=page_height, crop_to_cover=True)

                # Draw the frame
                u.draw_frame(frame_right_x, frame_top_y, c, width=frame_width, height=FRAME_HEIGHT, border_thickness=FRAME_BORDER_THICKNESS, h_align=u.H_ALIGN_RIGHT, v_align=u.V_ALIGN_TOP)

                # Write the set's name and alternative name, if present
                title_y = frame_centre_y
                subtitle_y = frame_centre_y
                if set_name and set_name_alt:
                    title_y = frame_centre_y + (TITLE_SIZE+TEXT_SIZE)/2 - TITLE_SIZE/2
                    subtitle_y = frame_centre_y - (TITLE_SIZE+TEXT_SIZE)/2 + TEXT_SIZE/2
                if set_name:
                    u.write_text(set_name, frame_centre_x, title_y, c, font_weight=u.FONT_WEIGHT_BOLD, font_size=TITLE_SIZE, h_align=u.H_ALIGN_CENTRE, v_align=u.V_ALIGN_MIDDLE)
                if set_name_alt:
                    u.write_text(set_name_alt, frame_centre_x, subtitle_y, c, font_size=TEXT_SIZE, h_align=u.H_ALIGN_CENTRE, v_align=u.V_ALIGN_MIDDLE)

                # Write the serie name in the top-left corner, if present
                if serie_name:
                    u.write_text(serie_name, padded_frame_left_x, padded_frame_top_y, c, font_weight=u.FONT_WEIGHT_BOLD, font_size=TEXT_SIZE, h_align=u.H_ALIGN_LEFT, v_align=u.V_ALIGN_TOP)

                # Write the date in the bottom-right corner, if present
                if set_date:
                    u.write_text(set_date, padded_frame_right_x, padded_frame_bottom_y, c, font_weight=u.FONT_WEIGHT_BOLD, font_size=TEXT_SIZE, h_align=u.H_ALIGN_RIGHT, v_align=u.V_ALIGN_BOTTOM)

                # Draw the symbol(s), if present
                symbol_x = padded_frame_left_x
                for symbol_path in set_symbol_paths:
                    u.draw_image(symbol_path, symbol_x, padded_frame_bottom_y, c, width=SYMBOL_WIDTH)
                    symbol_x = symbol_x + SYMBOL_WIDTH + SYMBOL_PADDING

                # Draw the region symbol, if specified
                if region_filename:
                    region_path = os.path.join(data.imgs_dir_path, region_filename)
                    u.draw_image(region_path, padded_frame_right_x, padded_frame_top_y, c, width=region_symbol_width, h_align=u.H_ALIGN_RIGHT, v_align=u.V_ALIGN_TOP, border_width=1)

                # Render the page
                c.showPage()

        u.log("")

        # Save and close the PDF document
        c.save()
