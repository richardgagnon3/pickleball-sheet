import argparse
import logging
import os
import pandas as pd

from games_table import GamesTable
from player import Player, PlayerStatistics
from sheet_reader import SheetReader

LEVEL_ARGS = ["debug", "info", "warning", "error"]
LEVEL_ARGS_SHORT = ["d", "i", "w", "e"]
ARGS_TO_LEVEL = {
    "d": logging.DEBUG,
    "debug": logging.DEBUG,
    "i": logging.INFO,
    "info": logging.INFO,
    "w": logging.WARNING,
    "warning": logging.WARNING,
    "e": logging.ERROR,
    "error": logging.ERROR,
}
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
_parser.add_argument(
    "-l",
    "--level",
    type=str,
    default="info",
    help="Log level",
    choices=LEVEL_ARGS + LEVEL_ARGS_SHORT,
)  # log level
args = _parser.parse_args()
_logger.setLevel(ARGS_TO_LEVEL[args.level])
_logger.debug("CSV File: %s, log level: %s", args.csv_file, args.level)

csv_file = args.csv_file
if not os.path.isfile(csv_file):
    _logger.error("File %s does not exist!", csv_file)
    exit(1)

try:
    csv_reader = SheetReader(csv_file)
    file_data = csv_reader.read()
    game_table = GamesTable(file_data)
    if args.show:
        game_table.print()

    players_list = game_table.get_players_list()
    players_stat = {}
    for p in players_list:
        player = Player(p)
        stats = PlayerStatistics(player)
        stats.analyze_benching(game_table)
        players_stat[p] = stats

    if _logger.isEnabledFor(logging.DEBUG):
        print_header = True
        for player, stats in players_stat.items():
            stats.print(print_header)
            print_header = False

    # TODO Compute stats about overall players playing time
    overall_stats = pd.DataFrame()
    overall_stats_columns = [
        "player",
        "games",
        "pauses",
        "inter_bench_min",
        "inter_bench_avg",
        "inter_bench_max",
        "inter_bench_std",
        "inter_bench_var",
    ]
    overall_stats = pd.DataFrame(columns=overall_stats_columns)
    for player, stats in players_stat.items():
        player_stats = stats.toDict()
        overall_stats = overall_stats.merge(
            pd.DataFrame([player_stats], columns=overall_stats_columns),
            how="outer",)
    if _logger.isEnabledFor(logging.DEBUG):
        print("\nOverall statistics data frame:")
        print(overall_stats.to_string(index=False))

    # First criteria (lower is better): Number of played games standard deviation
    #    - 0 means everybody has played the same number of games
    #     - A sub-criteria could be that the difference between min and max should not be greater than 1.
    # Second criteria (lower is better): Average games played between pauses standard deviation
    #     - low deviation means that players have similar playing times between benching
    #     - A sub-criteria could be that inter_bench_min cannot be 0 (would mean a player is benching twice in a row).
except Exception as e:
    _logger.error(f"Exception raised: {e}")
    exit(1)
