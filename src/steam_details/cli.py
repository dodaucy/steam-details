from argparse import ArgumentParser

parser = ArgumentParser(
    prog="steam_details",
    description="Displays some details for a steam app or a whole wishlist.",
    epilog="If you find bugs or have suggestions, please open an issue at https://github.com/dodaucy/steam-details/issues/new/choose",
)

parser.add_argument(
    "-v", "--version", action="store_true", help="Show the version and exit."
)

args = parser.parse_args()
