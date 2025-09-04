import csv
import logging

_logger = logging.getLogger("__main__")


class SheetReader:
    _logger = _logger

    def __init__(self, filename: str) -> None:
        self._logger.debug("New %s object created", self.__class__.__name__)
        self._csv_file = filename

    def read(self) -> list:
        game_table = []
        with open(self._csv_file, newline="", encoding="utf-8") as csv_file:
            self._logger.info("Reading CSV file: %s ...", self._csv_file)
            reader = csv.reader(csv_file, delimiter=",")  # , quotechar='|'
            is_new_court = False
            court_name = None
            in_pause = False
            game_tags = []
            nb_of_games = 0
            for row in reader:
                # Remove spaces from all entries in row.
                for i in range(len(row)):
                    if isinstance(row[i], str):
                        row[i] = row[i].strip()
                while len(row) and row[len(row) - 1] == "":
                    row.pop()
                self._logger.debug("Analyzing row: %s", " : ".join(row))
                if len(game_tags) == 0 and not row[0].startswith("Terrain"):
                    game_tags = row
                    nb_of_games = len(game_tags)
                    for i in range(nb_of_games):
                        game_table.append({"Game": game_tags[i]})

                elif row[0].startswith("Terrain"):
                    court_name = self.extract_court_name(row[0])
                    is_new_court = True
                    self._logger.info("New court: %s", court_name)

                elif row[0] == "Pause":
                    if in_pause:
                        self._logger.error("Too many Pause section in file!")
                    else:
                        in_pause = True
                        self._logger.info("Reading pause section ...")
                        for i in range(len(game_tags)):
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
                            self._logger.error(
                                "Too many players in game %s on court %s",
                                game_table[i]["Game"],
                                court_name,
                            )

        return game_table

    def extract_court_name(self, line):
        return line
