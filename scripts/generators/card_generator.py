import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
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
                set_name_width = 0
                if "name" in set:
                    set_name = set["name"]
                    set_name_width = u.get_text_width(set_name, font_weight=u.FONT_WEIGHT_BOLD, font_size=TITLE_SIZE)

                # Get the set alt name, if present
                set_name_alt = None
                set_name_alt_width = 0
                if "name_alt" in set:
                    set_name_alt = set["name_alt"]
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
                set_print_str = f"{page}.{card_in_page}. {set_print_name}"
                if not has_printed_serie:
                    u.log(f"\n{serie_print_name}")
                    has_printed_serie = True
                u.log(set_print_str, 1)

                # Get the set region symbol, if specified
                region_filename = None
                region_symbol_width = 0
                if "region" in set:
                    set_region = set["region"]
                    if set_region in self.config.region_filenames:
                        region_filename = self.config.region_filenames[set_region]
                        region_symbol_width = SYMBOL_WIDTH

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
                        if file.startswith(self.config.cover_filename_prefix):
                            set_cover_path = os.path.join(set_dir_path, file)
                        if file.startswith(self.config.symbol_filename_prefix):
                            symbol_path = os.path.join(set_dir_path, file)
                            set_symbol_paths.append(symbol_path)
                set_symbols_tot_width = len(set_symbol_paths)*SYMBOL_WIDTH + max(0, len(set_symbol_paths)-1)*SYMBOL_PADDING

                card_col = (card_in_page-1)%3
                card_row = (card_in_page-1)//3

                card_x = card_col*card_width + (card_col+1)*card_spacing_h
                card_y = page_height - (card_row*card_height + (card_row+1)*card_spacing_v)

                # Draw the cover, if present
                if set_cover_path:
                    u.draw_image(set_cover_path, card_x, card_y, c, width=card_width, height=card_height, crop_to_cover=True, h_align=u.H_ALIGN_LEFT, v_align=u.V_ALIGN_TOP)

                # Draw the frame
                u.draw_frame(card_x, card_y-card_height, c, width=card_width, height=card_height/2, border_thickness=FRAME_BORDER_THICKNESS, h_align=u.H_ALIGN_LEFT, v_align=u.V_ALIGN_BOTTOM, is_full_size=True)

                if (card_in_page == 9):
                    # Render the page
                    c.showPage()

        if (card_in_page < 9):
            # Render the page
            c.showPage()

        u.log("")

        # Save and close the PDF document
        c.save()
