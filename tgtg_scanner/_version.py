import importlib.metadata

PAKAGE_NAME = "tgtg_scanner"

metadata = importlib.metadata.metadata(PAKAGE_NAME)

__title__ = metadata["Name"]
__description__ = metadata["Summary"]
__version__ = importlib.metadata.version(PAKAGE_NAME)
__author__ = metadata["Author"]
__author_email__ = metadata["Author-email"]
__license__ = metadata["License"]
__url__ = metadata["Project-URL"].split(", ")[1]
