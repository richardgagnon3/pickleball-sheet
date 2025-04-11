import pytest
import os
from sheet_reader import SheetReader
from games_table import GamesTable

# Set default directory for games files as the parent directory of this file.
GAMES_TABLE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "games"
)

class TestGamesTable:

    def _load_games_csv(self, filename):
        reader = SheetReader(filename)
        game_table_raw = reader.read()
        return game_table_raw

    def test_get_games_table_from_good_file(self):
        games_file = os.path.join(GAMES_TABLE_DIR, "11j-2t.csv")
        expected_players = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11']#, '12', '13', '14', '15', '16']
        game_table_raw = self._load_games_csv(games_file)
        game_table = GamesTable(game_table_raw)
        # 2 simple checks to see it worked: print and check player list
        game_table.print()
        player_list = game_table.get_players_list()
        print(player_list)
        assert(player_list == expected_players)

    def test_get_games_table_for_6_players(self):
        games_file = os.path.join(GAMES_TABLE_DIR, "06j-1t.csv")
        expected_players = ['1', '2', '3', '4', '5', '6']
        game_table_raw = self._load_games_csv(games_file)
        game_table = GamesTable(game_table_raw)
        # 2 simple checks to see it worked: print and check player list
        game_table.print()
        player_list = game_table.get_players_list()
        print(player_list)
        assert(player_list == expected_players)

    def test_get_games_table_from_bad_file(self):
        games_file = os.path.join(GAMES_TABLE_DIR, "06j-1t-error.csv")
        game_table_raw = self._load_games_csv(games_file)
        with pytest.raises(Exception) as exc_info:
            game_table = GamesTable(game_table_raw)
        assert str(exc_info.value) == 'Something wrong in games table'
