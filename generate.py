import os
import shutil

from scripts.generators.page_generator import *
from scripts.generators.card_generator import *
from scripts.generator_data import GeneratorData

# Links:
# https://bulbapedia.bulbagarden.net/wiki/List_of_Pok%C3%A9mon_Trading_Card_Game_expansions
# https://bulbapedia.bulbagarden.net/wiki/List_of_Japanese_Pok%C3%A9mon_Trading_Card_Game_expansions

# TODO
# Choose better covers for some promo sets (instead of a card from the set)
# Add all existing sets
# Add a README.md and licence

# Get the directory path of the script
script_dir_path = os.path.dirname(os.path.abspath(__file__))

# Get paths
catalog_dir_path = os.path.join(script_dir_path, "catalog")
catalog_file_path = os.path.join(catalog_dir_path, "catalog.json")
output_file_path = os.path.join(script_dir_path, "headers.pdf")
assets_dir_path = os.path.join(script_dir_path, "assets")
imgs_dir_path = os.path.join(assets_dir_path, "imgs")
frame_imgs_dir_path = os.path.join(imgs_dir_path, "frame")
catalog_assets_dir_path = os.path.join(catalog_dir_path, "assets")
fonts_dir_path = os.path.join(assets_dir_path, "fonts")
config_file_path = os.path.join(script_dir_path, "config.yaml")
example_config_file_path = os.path.join(script_dir_path, "config.example.yaml")

# Initialise the utils module
u.init(fonts_dir_path, frame_imgs_dir_path)

# Parse the catalog data from the catalog JSON file
catalog = u.parse_json(catalog_file_path)

# Parse the config.yaml file
if not os.path.exists(config_file_path):
    u.log(f"Generating config file at {config_file_path}")
    shutil.copy(example_config_file_path, config_file_path)
config = u.parse_yaml(config_file_path)

# Set up the data object for the generator
generator_data = GeneratorData(
    catalog = catalog,
    config = config,
    output_file_path = output_file_path,
    catalog_sets_dir_path = catalog_assets_dir_path,
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

# Choose the correct generator
headers_type = config["headers_type"]
if headers_type == "cards":
    generator = CardGenerator()
elif headers_type == "pages":
    generator = PageGenerator()
else:
    u.log(f"Uknown headers_type value \"{headers_type}\". Aborting.")
    exit(1)

# Generate the PDF
generator.generate(generator_data)
