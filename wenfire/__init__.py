"""WenFire - Financial Independence Calculator."""

try:
    from ._version import __version__, __version_tuple__
except ImportError:
    __version__ = "0.0.0+unknown"
    __version_tuple__ = (0, 0, 0, "+unknown")

__all__ = ["__version__", "__version_tuple__"]
