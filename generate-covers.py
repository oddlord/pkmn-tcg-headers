import os
import shutil

from scripts.generators.page_generator import *
from scripts.generators.card_generator import *
from scripts.config import Config

# Links:
# https://bulbapedia.bulbagarden.net/wiki/List_of_Pok%C3%A9mon_Trading_Card_Game_expansions
# https://bulbapedia.bulbagarden.net/wiki/List_of_Japanese_Pok%C3%A9mon_Trading_Card_Game_expansions

# TODO
# Choose better covers for some promo sets (instead of a card from the set)
# Rename the project to pkmn-tcg-headers, the main script to generate.py and the output file to headers.pdf

# Get the directory path of the script
script_dir_path = os.path.dirname(os.path.abspath(__file__))

# Get paths
catalog_dir_path = os.path.join(script_dir_path, "catalog")
catalog_file_path = os.path.join(catalog_dir_path, "catalog.json")
output_file_path = os.path.join(script_dir_path, "covers.pdf")
assets_dir_path = os.path.join(script_dir_path, "assets")
imgs_dir_path = os.path.join(assets_dir_path, "imgs")
frame_imgs_dir_path = os.path.join(imgs_dir_path, "frame")
catalog_sets_dir_path = os.path.join(catalog_dir_path, "sets")
fonts_dir_path = os.path.join(assets_dir_path, "fonts")
config_file_path = os.path.join(script_dir_path, "config.yaml")
example_config_file_path = os.path.join(script_dir_path, "config.example.yaml")

# Init the utils module
u.init(fonts_dir_path, frame_imgs_dir_path)

# Parse the catalog data from the catalog JSON file
catalog = u.parse_json(catalog_file_path)

if not os.path.exists(config_file_path):
    u.log(f"Generating config file at {config_file_path}")
    shutil.copy(example_config_file_path, config_file_path)
config_dict = u.parse_yaml(config_file_path)

# Set up the config object for the generator
config = Config(
    catalog = catalog,
    filters = config_dict["filters"],
    output_file_path = output_file_path,
    catalog_sets_dir_path = catalog_sets_dir_path,
    imgs_dir_path=imgs_dir_path,
    region_filenames = {
        # "all": "jpn-eng.jpg",
        "all": "eng-jpn.jpg",
        "eng": "eng.png",
        "jpn": "jpn.jpg"
    },
    cover_filename_prefix = "cover.",
    symbol_filename_prefix = "symbol"
)

# Generate the PDF
headers_type = config_dict["headers_type"]
if not headers_type or headers_type == "cards":
    generator = CardGenerator(config)
elif headers_type == "pages":
    generator = PageGenerator(config)
generator.generate()
