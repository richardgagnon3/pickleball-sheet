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

class BaseStatistics:
    _size = 0
    _avg = 0
    _min = 0
    _max = 0
    _var = 0
    _std = 0                              
    
    def __init__(self, data: list) -> None:
        self._data = list(data)
        self._size = len(self._data)
        self._avg = sum(self._data) / len(self._data)
        self._min = min(self._data)
        self._max = max(self._data)
        # Calculate standard deviation
        self._var = sum((x - self._avg) ** 2 for x in self._data) / len(self._data)
        self._std = self._var ** 0.5

    def __str__(self):
        return f"Size={self._size}, Avg={self._avg}, Min={self._min}, Max={self._max} : {self._data}"

    @property
    def avg(self):
        return self._avg
    @property
    def min(self):
        return self._min
    @property
    def max(self):
        return self._max
    @property
    def std(self):
        return self._std
    @property
    def var(self):
        return self._var
    
class PlayerStatistics:
    _logger = _logger

    def __init__(self, player: Player) -> None:
        self._player = player
        self._bench_seq = []
        self._game_seq = []
        self._nb_pauses = 0
        self._nb_games = 0
        self._between_pause_stats = None
        self._logger.debug(f"New {self.__class__.__name__} object created for player {self._player}")

    def analyze_games(self, game_table: GamesTable):
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
        self._logger.info(f"Between pause stats for player {self._player.name}: {self._between_pause_stats}")
        # TODO Like in Excel, build cumulative benching array.
        # TODO Analyze consecutive benching, nb of game between benching, ...
        #self._logger.info(f"Player {self._player.name} benched {self._nb_pauses} times for games: {benched_games}")

    def print(self, print_header: bool = False):
        format_heading = "|%6s|%6s|%6s|%5s|%5s|%5s|%5s|%5s|%s"
        format_data    = "|%6s|%6d|%6d|%5d|%5.1f|%5d|%5.2f|%5.2f|%s"
        if print_header:
            print( "-"*70 )
            print(format_heading % ("Player", 
                                    "Games", 
                                    "Pauses", 
                                    "Min", 
                                    "Avg", 
                                    "Max", 
                                    "Std", 
                                    "Var",
                                    "Games between pauses"))
            print( "-"*80 )
        print(format_data % (self._player.name, 
              self._nb_games, 
              self._nb_pauses, 
              self._between_pause_stats.min, 
              self._between_pause_stats.avg, 
              self._between_pause_stats.max, 
              self._between_pause_stats.std, 
              self._between_pause_stats.var,
              str(self._between_pause_stats._data)))
        print( "-"*80 )