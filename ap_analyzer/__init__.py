"""ap_analyzer package init"""
from importlib.metadata import version, PackageNotFoundError
try:
    __version__ = version("ap_analyzer")
except PackageNotFoundError:
    __version__ = "0.dev0"
