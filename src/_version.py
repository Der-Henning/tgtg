import importlib.metadata

metadata = importlib.metadata.metadata("tgtg")

__title__ = metadata.get("Name")
__description__ = metadata.get("Description")
__version__ = importlib.metadata.version("tgtg")
__author__ = metadata.get("Author")
__author_email__ = metadata.get("Author-email")
__license__ = metadata.get("License")
__url__ = metadata.get("Project-URL").split(", ")[1]
