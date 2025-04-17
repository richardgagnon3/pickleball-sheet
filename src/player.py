import logging

from games_table import GamesTable

_logger = logging.getLogger("__main__")

class Player:
    _next_id = 1
    _logger = _logger

    def __init__(self, name: str, id: int = 0) -> None:
        self._name = name
        if id > 0:
            self._id = id
        else:
            self._id = Player._next_id
            Player._next_id += 1
        self._logger.debug(f"New {self.__class__.__name__} object created: Name={self._name}, ID={self._id}")

    def __str__(self) -> str:
        return f"Player {self._id}: name={self._name}"

    @property
    def name(self):
        return self._name
    

class PlayerStatistics:
    _logger = _logger

    def __init__(self, player: Player) -> None:
        self._player = player
        self._bench_seq = []
        self._game_seq = []
        self._logger.debug(f"New {self.__class__.__name__} object created for player {self._player}")

    def analyze_games(self, game_table: GamesTable):
        self._bench_seq = game_table.get_bench(self._player.name)
        self._logger.debug(f"Player {self._player.name} benched {len(self._bench_seq)} times for games: {self._bench_seq}")
        # TODO Like in Excel, build cumulative benching array.
        # TODO Analyze consecutive benching, nb of game between benching, ...
