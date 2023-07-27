import importlib.metadata

PAKAGE_NAME = "tgtg_scanner"

metadata = importlib.metadata.metadata(PAKAGE_NAME)

__title__ = metadata.get("Name")
__description__ = metadata.get("Description")
__version__ = importlib.metadata.version(PAKAGE_NAME)
__author__ = metadata.get("Author")
__author_email__ = metadata.get("Author-email")
__license__ = metadata.get("License")
__url__ = metadata.get("Project-URL").split(", ")[1]
