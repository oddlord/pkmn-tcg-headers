# The data needed by generators to generate the headers
class GeneratorData():
    def __init__(
            self,
            catalog,
            config,
            output_file_path,
            catalog_sets_dir_path,
            imgs_dir_path,
            region_filenames,
            cover_filename_prefix,
            symbol_filename_prefix):
        self.catalog = catalog
        self.config = config
        self.output_file_path = output_file_path
        self.catalog_assets_dir_path = catalog_sets_dir_path
        self.imgs_dir_path = imgs_dir_path
        self.region_filenames = region_filenames
        self.cover_filename_prefix = cover_filename_prefix
        self.symbol_filename_prefix = symbol_filename_prefix
