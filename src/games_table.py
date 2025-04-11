import logging

class GamesTable:
    
    def __init__(self, table: dict) -> None:
        self._logger = logging.getLogger("__main__")
        self._logger.debug(f"New {self.__class__.__name__} object created")
        self._game_table = table


    def get_players_list(self) -> list:
        """
        Return a list of all players in the game table.

        The list is composed of all players that were either playing on a court or benched.
        """
        players = []
        court_list = list(self._game_table.keys())
        for court in court_list:
            games = self._game_table[court]
            game1 = games[list(games.keys())[0]]
            if court == "Bench":
                # Add all benched players
                players += game1
            else:
                # For each court, read players in first game.
                players += game1['Team1']
                players += game1['Team2']
        # Find longest player name
        longest_name = 0
        for player in players:
            if len(player) > longest_name:
                longest_name = len(player)
        # Add leading spaces to player names
        # when the name is a number.
        for i in range(len(players)):
            try:
                int(players[i])
                while len(players[i]) < longest_name:
                    players[i] = " " + players[i]
            except ValueError:
                pass
        # Sort players in alphabetical order
        players.sort()
        for i in range(len(players)):
            players[i] = players[i].strip()
        return players

    def get_bench(self, player=None):
        bench_list = []
        if player is None:
            return bench_list
        games = self._game_table["Bench"]
        cumulative_benching = 0
        for game in games.keys():
            if player in games[game]:
                cumulative_benching += 1
            bench_list.append(cumulative_benching)
        return bench_list
    
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
            if court == "Bench":
                has_bench = True
            else:
                self.print_court(court)

        if has_bench:
            self.print_bench()

