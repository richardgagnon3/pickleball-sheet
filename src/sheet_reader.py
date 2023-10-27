import csv
import logging


class SheetReader:
    def __init__(self, filename: str) -> None:
        self._logger = logging.getLogger(__class__.__name__)
        self._logger.setLevel(logging.DEBUG)
        # create console handler and set level to debug
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        # add ch to logger
        self._logger.addHandler(ch)
        self._logger.debug(f"New {self.__class__.__name__} object created")
        self._csv_file = filename

    def read(self):
        game_table = {}
        with open(self._csv_file, newline="") as csvfile:
            self._logger.info(f"Reading CSV file: {self._csv_file} ...")
            reader = csv.reader(csvfile, delimiter=",")  # , quotechar='|'
            is_new_court = False
            in_pause = False
            game_tags = []
            nb_of_games = 0
            for row in reader:
                while len(row) and row[len(row) - 1] == "":
                    row.pop()
                self._logger.debug(f"Analyzing row: {' : '.join(row)}")
                if row[0].startswith("Terrain"):
                    court_name = self.extract_court_name(row[0])
                    is_new_court = True
                    self._logger.info(f"New court: {court_name}")
                elif row[0] == "Pause":
                    if in_pause:
                        self._logger.error(f"Too many Pause section in file!")
                    else:
                        in_pause = True
                        self._logger.info(f"Reading pause section ...")
                        game_table["Bench"] = {}
                        for i, game in enumerate(game_tags):
                            game_table["Bench"][game] = []
                elif is_new_court:
                    if len(game_tags) == 0:
                        game_tags = row
                        nb_of_games = len(game_tags)
                    else:
                        game_table[court_name] = {}
                        is_new_court = False
                        for i, game in enumerate(game_tags):
                            game_table[court_name][game] = {
                                "Team1": [row[i]],
                                "Team2": [],
                            }

                elif in_pause:
                    for i, game in enumerate(game_tags):
                        game_table["Bench"][game] += [row[i]]

                else:
                    t1 = game_table[court_name][game]["Team1"]
                    t2 = game_table[court_name][game]["Team2"]
                    if len(game_table[court_name][game]["Team1"]) == 1:
                        for i, game in enumerate(game_tags):
                            p = row[i]
                            t = game_table[court_name][game]["Team1"]
                            game_table[court_name][game]["Team1"] += [row[i]]
                    elif len(game_table[court_name][game]["Team2"]) < 2:
                        for i, game in enumerate(game_tags):
                            game_table[court_name][game]["Team2"] += [row[i]]

        return game_table

    def extract_court_name(self, line):
        return line
