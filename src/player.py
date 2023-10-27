import logging

from games_table import GamesTable

class Player:
    _next_id = 1

    def __init__(self, name: str, id: int = 0) -> None:
        self._logger = logging.getLogger(__class__.__name__)
        self._logger.setLevel(logging.DEBUG)
        # create console handler and set level to debug
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        # add ch to logger
        self._logger.addHandler(ch)
        self._logger.debug(f"New {self.__class__.__name__} object created")
        self._name = name
        if id > 0:
            self._id = id
        else:
            self._id = Player._next_id
            Player._next_id += 1

    def __str__(self) -> str:
        return f"Player {self._id}: name={self._name}"

    @property
    def name(self):
        return self._name
    

class PlayerStatistics:

    def __init__(self, player: Player) -> None:
        self._logger = logging.getLogger(__class__.__name__)
        self._logger.setLevel(logging.DEBUG)
        # create console handler and set level to debug
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        # add ch to logger
        self._logger.addHandler(ch)
        self._logger.debug(f"New {self.__class__.__name__} object created")
        self._player = player
        self._bench_seq = []
        self._game_seq = []

    def analyze_games(self, game_table: GamesTable):
        bench = game_table.get_bench(self._player.name)
        self._logger.debug(f"Player {self._player.name} benched {len(bench)} times as: {bench}")
        # TODO Like in Excel, build cumulative benching array.
        # TODO Analyze consecutive benching, nb of game between benching, ...
