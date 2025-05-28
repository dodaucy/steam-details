from argparse import ArgumentParser

parser = ArgumentParser(
    prog="steam_details",
    description="Displays some details for a steam app or a whole wishlist.",
    epilog="If you find bugs or have suggestions, please open an issue at https://github.com/dodaucy/steam-details/issues/new/choose",
)

# Version
parser.add_argument(
    "-v", "--version", action="store_true", help="Show the version and exit."
)

# Logging
logging_group = parser.add_argument_group(title="Logging")
logging_group.add_argument(
    "-l",
    "--log-level",
    type=str,
    default="INFO",
    choices=("DEBUG", "INFO", "WARNING", "ERROR"),
    help="Set the logging level."
)
logging_group.add_argument(
    "--no-colors",
    action="store_true",
    help="Disable colors in the logging output."
)

# Hosting
hosting_group = parser.add_argument_group(title="Hosting")
hosting_group.add_argument(
    "--host",
    type=str,
    default="127.0.0.1",
    help="The host to listen on. DO NOT MAKE THIS PUBLIC."
)
hosting_group.add_argument(
    "-p",
    "--port",
    type=int,
    default=8000,
    help="The port to listen on."
)

# Other
other_group = parser.add_argument_group(title="Other")
other_group.add_argument(
    "--cache-timeout",
    type=int,
    default=60 * 60,
    help="The timeout in seconds for the cache."
)


args = parser.parse_args()
