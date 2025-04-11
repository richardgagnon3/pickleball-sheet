import pytest
from sheet_reader import SheetReader
from games_table import GamesTable


class TestSheetReader:

    def test_file_does_not_exist(self):
        reader = SheetReader("bad_filename.csv")
        with pytest.raises(FileNotFoundError):
            reader.read()

    def test_read_csv_file(self):
        reader = SheetReader('/'.join(["pickleball-sheet/games" , "11j-2t.csv"]))
        game_table_raw = reader.read()
        #print(str(game_table_raw))
        assert "Terrain 2" in game_table_raw

    # TODO: Add test where csv file does not have 4 players per court.
    
    # TODO: Add test where csv file does not have same number of games for a court. 