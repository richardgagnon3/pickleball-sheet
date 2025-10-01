import logging

from base_statistics import BaseStatistics
from games_table import GamesTable

_logger = logging.getLogger("__main__")

class Player:
    _next_id = 1
    _logger = _logger

    def __init__(self, name: str, player_id: int = 0) -> None:
        self._name = name
        if player_id > 0:
            self._id = player_id
        else:
            self._id = Player._next_id
            Player._next_id += 1
        self._logger.debug("New %s object created: Name=%s, ID=%d", self.__class__.__name__, self._name, self._id)

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
        self._nb_pauses = 0
        self._nb_games = 0
        self._between_pause_stats: BaseStatistics | None = None
        self._logger.debug("New %s object created for player %s", self.__class__.__name__, self._player)

    def analyze_benching(self, game_table: GamesTable):
        self._bench_seq = game_table.get_bench(self._player.name)
        benched_games = list(set(self._bench_seq) - {0})
        benched_games.sort()
        self._nb_pauses = len(benched_games)
        self._nb_games = len(self._bench_seq) - self._nb_pauses
        games_between_pauses = []
        consecutive_played_games = 0
        game_index = 0
        for i in self._bench_seq:
            if i == 0:
                consecutive_played_games += 1
                game_index += 1
                continue
            if game_index == 0:
                game_index += 1
                continue
            games_between_pauses.append(consecutive_played_games)
            consecutive_played_games = 0
            game_index += 1
        if consecutive_played_games > 0:
            games_between_pauses.append(consecutive_played_games)
        self._between_pause_stats = BaseStatistics(games_between_pauses)
        self._logger.info("Between pause stats for player %s: %s", self._player.name, self._between_pause_stats)

    def print(self, print_header: bool = False):
        format_heading = "|%6s|%6s|%6s|%5s|%5s|%5s|%5s|%5s|%s"
        format_data    = "|%6s|%6d|%6d|%5d|%5.1f|%5d|%5.2f|%5.2f|%s"
        if print_header:
            print( "="*75 )
            print(format_heading % ("Player", 
                                    "Games", 
                                    "Pauses", 
                                    "Min", 
                                    "Avg", 
                                    "Max", 
                                    "Std", 
                                    "Var",
                                    "Games between pauses"))
            print( "="*75 )
        print(format_data % (self._player.name, 
              self._nb_games, 
              self._nb_pauses, 
              self._between_pause_stats.min, 
              self._between_pause_stats.avg, 
              self._between_pause_stats.max, 
              self._between_pause_stats.std, 
              self._between_pause_stats.var,
              str(self._between_pause_stats.data)))
        print( "-"*75 )

    def toDict(self) -> dict:
        if self._between_pause_stats:
            return {
                "player": self._player.name,
                "games": self._nb_games,
                "pauses": self._nb_pauses,
                "inter_bench_min": self._between_pause_stats.min,
                "inter_bench_avg": self._between_pause_stats.avg,
                "inter_bench_max": self._between_pause_stats.max,
                "inter_bench_std": self._between_pause_stats.std,
                "inter_bench_var": self._between_pause_stats.var,
            }
        else:
            return {
                "player": self._player.name,
                "games": self._nb_games,
                "pauses": self._nb_pauses,
            }

    @property
    def games_between_pauses(self) -> list:
        return self._between_pause_stats.data if self._between_pause_stats else []
