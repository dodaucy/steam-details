from argparse import ArgumentParser


parser = ArgumentParser()
parser.add_argument(
    "-v", "--version", action="store_true", help="Show the version and exit."
)

args = parser.parse_args()
