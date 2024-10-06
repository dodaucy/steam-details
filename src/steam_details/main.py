import logging
from argparse import ArgumentParser

import uvicorn

from .utils import ANSICodes
from .web.web import app


class ColorFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: ANSICodes.GREEN,
        logging.INFO: ANSICodes.BLUE,
        logging.WARNING: ANSICodes.YELLOW,
        logging.ERROR: ANSICodes.RED,
        logging.CRITICAL: ANSICodes.MAGENTA
    }

    def format(self, record: logging.LogRecord) -> str:  # noqa: D102
        return super().format(record).replace(
            "{LEVEL_COLOR}",
            self.COLORS.get(record.levelno, ANSICodes.RESET),
            1
        )


def main() -> int:
    """Display some details for a steam app or a whole wishlist."""
    # Logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d) %(message)s",
        handlers=[
            logging.StreamHandler()
        ]
    )
    logging.getLogger().handlers[0].setFormatter(ColorFormatter(
        f"%(asctime)s {{LEVEL_COLOR}}{ANSICodes.BOLD}[%(levelname)s]{ANSICodes.RESET} %(name)s ({ANSICodes.BLUE}%(filename)s:%(lineno)d{ANSICodes.RESET}) %(message)s"  # noqa
    ))

    parser = ArgumentParser()
    parser.add_argument(
        "-V", "--version", action="store_true", help="Show the version and exit."
    )

    args = parser.parse_args()

    if args.version:
        from . import __version__
        print(f"Steam Details {__version__}")
        return 0

    uvicorn.run(app, host="127.0.0.1", port=8000)

    return 0
