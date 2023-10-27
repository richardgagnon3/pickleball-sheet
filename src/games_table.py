import logging

class GamesTable:

    def __init__(self, table: dict) -> None:
        self._logger = logging.getLogger(__class__.__name__)
        self._logger.setLevel(logging.DEBUG)
        # create console handler and set level to debug
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        # add ch to logger
        self._logger.addHandler(ch)
        self._logger.debug(f"New {self.__class__.__name__} object created")
        self._game_table = table

    def get_players_list(self) -> list:
        # TODO Go over all courts and bench to build a list of players
        return []

    def get_bench(self, player=None):
        # TODO : Build array of benched player(s)
        return []
    
    def print_court(self, court_name):
        games = self._game_table[court_name]
        print(f"/------------------------\\")
        print(f"|    Court: {court_name:12s} |")
        grid = ['+--------+',
                '| Game   |',
                '|--------|',
                '| Team 1 |',
                '|        |',
                '| Team 2 |',
                '|--------|',
                ]
        for game in games.keys():
            grid[0] += f"-------|"
            grid[1] += f" {game:^5s} |"
            grid[2] += f"-------|"
            player = [games[game]['Team1'][0], games[game]['Team1'][1]]
            grid[3] += f" {player[0]:>2s},{player[1]:<2s} |"
            grid[4] += f"   vs  |"
            player = [games[game]['Team2'][0], games[game]['Team2'][1]]
            grid[5] += f" {player[0]:>2s},{player[1]:<2s} |"
            grid[6] += f"-------+"

        for line in grid:
            print(line)

    def print_bench(self):
        name = "Bench"
        games = self._game_table[name]
        print(f"/----------------\\")
        print(f"|   {name:12s} |")
        grid = ['+--------+',
                '| Game   |',
                '|--------+',
                ]
        game_list = list(games.keys())
        nb_benched_players = len(games[game_list[0]])
        for i in range(nb_benched_players):
            grid.append('|        |')
        grid.append('+--------+')
        for game in game_list:
            grid[0] += f"-------+"
            grid[1] += f" {game:^5s} |"
            grid[2] += f"-------+"
            for i in range(nb_benched_players):
                player = games[game][i]
                grid[3+i] += f" {player:^5s} |"
            grid[3+nb_benched_players] += f"-------+"

        for line in grid:
            print(line)

    def print(self):
        has_bench = False
        court_list = list(self._game_table.keys())
        for court in court_list:
            if court is "Bench":
                has_bench = True
            else:
                self.print_court(court)

        if has_bench:
            self.print_bench()

