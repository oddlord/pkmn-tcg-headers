import os
from argparse import ArgumentParser

from scripts.generators.page_generator import *
from scripts.generators.card_generator import *
from scripts.config import Config

# Links:
# https://bulbapedia.bulbagarden.net/wiki/List_of_Pok%C3%A9mon_Trading_Card_Game_expansions
# https://bulbapedia.bulbagarden.net/wiki/List_of_Japanese_Pok%C3%A9mon_Trading_Card_Game_expansions

# TODO move to their own sets
# Remove V placeholders
# Eevee Heroes puzzle card???
# maybe others...?


# Get the directory path of the script
script_directory = os.path.dirname(os.path.abspath(__file__))

# Get paths
catalog_file_path = os.path.join(script_directory, "catalog.json")
output_file_path = os.path.join(script_directory, "covers.pdf")
imgs_dir_path = os.path.join(script_directory, "assets/imgs")
frame_imgs_dir_path = os.path.join(script_directory, "assets/imgs/frame")
catalog_assets_dir_path = os.path.join(script_directory, "assets/catalog")
fonts_dir_path = os.path.join(script_directory, "assets/fonts")

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

# Parse the catalog data from the catalog JSON file
catalog = u.parse_json(catalog_file_path)

# Parse the filter JSON file
filtered_sets = None
if args.filter_filename:
    filter_file_path = os.path.join(script_directory, args.filter_filename)
    filtered_sets = u.parse_json(filter_file_path)

# Set up the config object for the generator
config = Config(
    catalog = catalog,
    filtered_sets = filtered_sets,
    output_file_path = output_file_path,
    catalog_assets_dir_path = catalog_assets_dir_path,
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
# generator = PageGenerator(config)
generator = CardGenerator(config)
generator.generate()
