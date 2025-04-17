import argparse
import logging
import os

from games_table import GamesTable
from player import Player, PlayerStatistics
from sheet_reader import SheetReader

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)
_logger.info("Running %s", __file__)
# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# add ch to logger
_logger.addHandler(ch)
# Add log level into logged messages.
formatter = logging.Formatter('%(levelname)s: %(message)s')
ch.setFormatter(formatter)
_logger.info('Starting the analysis program.')

_parser = argparse.ArgumentParser(
    prog="sheet_evaluator",
    description="Reads a pickleball games sheet and provide statistics about the games for a given period of time.",
    epilog="Statistics includes: pause_time/player, average_games/pause",
)

_parser.add_argument("csv_file")  # Input file with games/courts
_parser.add_argument("-s", "--show", action="store_true", help="Show the game table read from the input file")
_parser.add_argument("-l", "--level", choices=[10, 20, 30, 40, 50], type=int, default=20)  # log level
args = _parser.parse_args()
# TODO: Validate level value (or force a list of levels for argument -l)
_logger.setLevel(args.level)
_logger.debug(f"CSV File: {args.csv_file}, log level: {args.level}")

csv_file = args.csv_file
if not os.path.isfile(csv_file):
    _logger.error(f"File {csv_file} does not exist!")
    exit(1)

try:
    csv_reader = SheetReader(csv_file)
    game_table = GamesTable(csv_reader.read())
    if args.show:
        game_table.print()

    players_list = game_table.get_players_list()
    players_stat = {}
    for p in players_list:
        player = Player(p)
        stats = PlayerStatistics(player)
        stats.analyze_games(game_table)
        players_stat[p] = stats
except Exception as e:
    _logger.error(f"Exception raised: {e}")
    exit(1)

