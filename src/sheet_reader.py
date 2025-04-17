import csv
import logging

_logger = logging.getLogger("__main__")

class SheetReader:
    _logger = _logger
    
    def __init__(self, filename: str) -> None:
        self._logger.debug(f"New {self.__class__.__name__} object created")
        self._csv_file = filename

    def read(self):
        game_table = []
        with open(self._csv_file, newline="") as csv_file:
            self._logger.info(f"Reading CSV file: {self._csv_file} ...")
            reader = csv.reader(csv_file, delimiter=",")  # , quotechar='|'
            is_new_court = False
            court_name = None
            in_pause = False
            game_tags = []
            nb_of_games = 0
            for row in reader:
                while len(row) and row[len(row) - 1] == "":
                    row.pop()
                self._logger.debug(f"Analyzing row: {' : '.join(row)}")
                if len(game_tags) == 0 and not row[0].startswith("Terrain"):
                    game_tags = row
                    nb_of_games = len(game_tags)
                    for i in range(nb_of_games):
                        game_table.append({"Game" : game_tags[i]})

                elif row[0].startswith("Terrain"):
                    court_name = self.extract_court_name(row[0])
                    is_new_court = True
                    self._logger.info(f"New court: {court_name}")

                elif row[0] == "Pause":
                    if in_pause:
                        self._logger.error(f"Too many Pause section in file!")
                    else:
                        in_pause = True
                        self._logger.info(f"Reading pause section ...")
                        for i, game in enumerate(game_tags):
                            game_table[i]["Bench"] = []

                elif is_new_court:
                    is_new_court = False
                    for i, game in enumerate(game_tags):
                        game_table[i][court_name] = {
                            "Team1": [row[i]],
                            "Team2": [],
                        }

                elif in_pause:
                    for i, game in enumerate(game_tags):
                        game_table[i]["Bench"] += [row[i]]

                else:
                    for i, game in enumerate(game_tags):
                        if len(game_table[i][court_name]["Team1"]) == 1:
                            p = row[i]
                            t = game_table[i][court_name]["Team1"]
                            game_table[i][court_name]["Team1"] += [row[i]]
                        elif len(game_table[i][court_name]["Team2"]) < 2:
                            game_table[i][court_name]["Team2"] += [row[i]]
                        else:
                            self._logger.error(f"Too many players in game {game_table[i]['Game']} on court {court_name}")

        return game_table

    def extract_court_name(self, line):
        return line
