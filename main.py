# Tools libraries
from scraper.scraper import collect
from markread.markread import read

import argparse
import pathlib


parser = argparse.ArgumentParser(
    suggest_on_error=True,
    usage=None,
    prog="scrapper.py",
    description="scraps emails out of your google mails",
    epilog="No idea how to help",
)

# Tool select
parser.add_argument(
    "tool", choices=["scrape", "read"], help="Choose the tool to use")

# Arguments for scraper
parser.add_argument("-c", "--credentials", type=pathlib.Path)
parser.add_argument("-t", "--token", type=pathlib.Path)
parser.add_argument("-o", "--out", type=pathlib.Path)
parser.add_argument("-p", "--port", type=int, default=8080)
parser.add_argument(
    "-q",
    "--query",
    default="newer_than:1d",
    help="https://support.google.com/mail/answer/7190",
)


args = parser.parse_args()


if args.tool == "scrape":
    token_path, creds_path, output_path, port, query = (
        args.token,
        args.credentials,
        args.out,
        args.port,
        args.query,
    )
    collect(token_path, creds_path, output_path, port, query)
if args.tool == "read":
    token_path, creds_path, port = args.token, args.credentials, args.port
    read(token_path, creds_path, port)
