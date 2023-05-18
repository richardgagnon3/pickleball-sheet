import argparse
import logging

from sheet_reader import SheetReader

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)
_logger.info("Running %s", __file__)
# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# add ch to logger
_logger.addHandler(ch)

_logger.info('Starting the analysis program.')

_parser = argparse.ArgumentParser(
    prog="sheet_checker",
    description="Reads a pickleball games sheet and provide statistics about the games for a given period of time.",
    epilog="Statistics includes: pause_time/player, average_games/pause",
)

_parser.add_argument("csv_filename")  # Input file with games/courts
_parser.add_argument("-l", "--level", choices=[10, 20, 30, 40, 50], type=int)  # log level
args = _parser.parse_args()
# TODO: Validate level value (or force a list of levels for argument -l)
_logger.setLevel(args.level)
_logger.debug(f"CSV File: {args.csv_filename}, log level: {args.level}")

csv_directory = "pickleball-sheet/src"
csv_file = '/'.join([csv_directory , args.csv_filename])
csv_reader = SheetReader(csv_file)
csv_reader.read()
