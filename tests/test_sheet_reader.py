import pytest
from sheet_reader import SheetReader
from games_table import GamesTable


class TestSheetReader:

    def test_file_does_not_exist(self):
        reader = SheetReader("bad_filename.csv")
        with pytest.raises(FileNotFoundError):
            reader.read()

    def test_read_csv_file(self):
        reader = SheetReader('/'.join(["pickleball-sheet/src" , "11j-2t.csv"]))
        expected_players = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11']
        game_table_raw = reader.read()
        #print(str(game_table_raw))
        game_table = GamesTable(game_table_raw)
        game_table.print()
        # TODO: Move this player list check into its own test file.
        player_list = game_table.get_players_list()
        print(player_list)
        assert(player_list == expected_players)
        #assert False, f"No check developped!"

        