import logging

class GamesTable:
    
    def __init__(self, table: dict) -> None:
        self._logger = logging.getLogger("__main__")
        self._logger.debug(f"New {self.__class__.__name__} object created")
        self._game_table = table
        self._validate_table()

    def _validate_table(self):
        valid_games = True
        g1_players = self.get_players_list()
        for game in self._game_table:
            players = []
            for court in game:
                if court == "Game":
                    continue
                if court == "Bench":
                    players += game[court]
                    continue
                else:
                    if len(game[court]['Team1']) != 2:
                        self._logger.error(f"Bad number of players in Team 1 for Game {game['Game']} in {court}: {len(game[court]['Team1'])}")
                        valid_games = False
                    if len(game[court]['Team2']) != 2:
                        self._logger.error(f"Bad number of players in Team 2 for Game {game['Game']} in {court}: {len(game[court]['Team2'])}")
                        valid_games = False
                    players += game[court]['Team1']
                    players += game[court]['Team2']
            # Remove possible duplicate players
            unique_players = set(players)
            if len(unique_players) != len(players):
                if len(g1_players) > len(unique_players):
                    missing_players = set(g1_players) - unique_players
                else:
                    missing_players = unique_players - set(g1_players)
                dup_players = []
                while len(players):
                    player = players.pop()
                    if player in players:
                        dup_players.append(player)
                self._logger.error(f"Duplicate players {dup_players} in Game {game['Game']}, missing {missing_players}")
                valid_games = False
                continue
            # Check if new player appear in the game
            for player in players:
                if player not in g1_players:
                    self._logger.error(f"Player {player} is new in game {game['Game']} - must be in all games")
                    valid_games = False
            # Check if all players are in the game
            for player in g1_players:
                if player not in players:
                    self._logger.error(f"Player {player} is missing in game {game['Game']} - must be in all games")
                    valid_games = False
                    
        if not valid_games:
            raise Exception("Something wrong in games table")

    def get_games_list(self) -> list:
        """Returns the list of games contains into the game table.

        Returns:
            list: list of games identifiers
        """
        return [game['Game'] for game in self._game_table]

    def get_players_list(self) -> list:
        """
        Return a list of all players in the game table.

        The list is composed of all players that were either playing on a court or benched
        during the first game.
        """
        players = []
        game1 = self._game_table[0]
        court_list = list(game1.keys())
        for court in court_list:
            if court == "Game":
                # Game's name, no player in this element.
                continue
            if court == "Bench":
                # Add all benched players
                players += game1[court]
            else:
                # For each court, add players in each team.
                players += game1[court]['Team1']
                players += game1[court]['Team2']
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
        nb_games = len(self._game_table)
        # Initialize benching array with 0 for nb of games
        bench_list = [0] * nb_games
        if player is None:
            return bench_list
        for i, game in enumerate(self._game_table):
            bench = game.get("Bench", None)
            if player in bench:
                bench_list[i] = game['Game']
        return bench_list
    
    def print_court(self, court_name):
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
        for game in self._game_table:
            grid[0] += f"-------|"
            grid[1] += f" {game['Game']:^5s} |"
            grid[2] += f"-------|"
            player = [game[court_name]['Team1'][0], game[court_name]['Team1'][1]]
            grid[3] += f" {player[0]:>2s},{player[1]:<2s} |"
            grid[4] += f"   vs  |"
            player = [game[court_name]['Team2'][0], game[court_name]['Team2'][1]]
            grid[5] += f" {player[0]:>2s},{player[1]:<2s} |"
            grid[6] += f"-------+"

        for line in grid:
            print(line)

    def print_bench(self):
        bench_tag = "Bench"
        if bench_tag not in self._game_table[0]:
            return
        nb_benched_players = len(self._game_table[0][bench_tag])
        if nb_benched_players == 0:
            return
        
        print(f"/----------------\\")
        print(f"|   {bench_tag:12s} |")
        grid = ['+--------+',
                '| Game   |',
                '|--------+',
                ]
        for i in range(nb_benched_players):
            grid.append('|        |')
        grid.append('+--------+')
        for game in self._game_table:
            grid[0] += f"-------+"
            grid[1] += f" {game['Game']:^5s} |"
            grid[2] += f"-------+"
            for i in range(nb_benched_players):
                player = game[bench_tag][i]
                grid[3+i] += f" {player:^5s} |"
            grid[3+nb_benched_players] += f"-------+"

        for line in grid:
            print(line)

    def print(self):
        first_game = self._game_table[0]
        for court in first_game.keys():
            if court.startswith("Terrain"):
                self.print_court(court)
        self.print_bench()

