"""Displays some details for a steam app or a whole wishlist."""

from .cli import args

if __name__ == "__main__":
    if args.version:
        from . import __version__
        print(f"Steam Details {__version__}")
    else:
        from .main import main
        main()
