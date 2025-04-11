import logging

class GamesTable:
    
    def __init__(self, table: dict) -> None:
        self._logger = logging.getLogger("__main__")
        self._logger.debug(f"New {self.__class__.__name__} object created")
        self._game_table = table
        self._validate_table()


    def _validate_table(self):
        # Regroup table per games instead of per courts
        # TODO Should we change that into reader instead?
        games = {}
        valid_games = True
        for court in self._game_table:
            for game in self._game_table[court]:
                if game in games:
                    if court in games[game]:
                        self._logger.error(f"Game {game} is already in {court}")
                        valid_games = False
                        continue
                    games[game][court] = self._game_table[court][game]                    
                else:
                    games[game] = {court: self._game_table[court][game]}
        g1_players = self.get_players_list()
        for game in games:
            players = []
            for court in games[game]:
                if court == "Bench":
                    players += games[game][court]
                    continue
                else:
                    if len(games[game][court]['Team1']) != 2:
                        self._logger.error(f"Bad number of players in Team 1 for Game {game} in {court}: {len(games[game][court]['Team1'])}")
                        valid_games = False
                    if len(games[game][court]['Team2']) != 2:
                        self._logger.error(f"Bad number of players in Team 2 for Game {game} in {court}: {len(games[game][court]['Team1'])}")
                        valid_games = False
                    players += games[game][court]['Team1']
                    players += games[game][court]['Team2']
            # Remove possible duplicate players
            unique_players = list(set(players))
            if len(unique_players) != len(players):
                self._logger.error(f"Duplicate players in Game {game}")
                valid_games = False
                continue
            # Check if new player appear in the game
            for player in players:
                if player not in g1_players:
                    self._logger.error(f"Player {player} is new in game {game} - must be in all games")
                    valid_games = False
            # Check if all players are in the game
            for player in g1_players:
                if player not in players:
                    self._logger.error(f"Player {player} is missing in game {game} - must be in all games")
                    valid_games = False
                    
        if not valid_games:
            raise Exception("Something wrong in games table")
                
                
                
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

