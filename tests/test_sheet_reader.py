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
        game_table_raw = reader.read()
        #print(str(game_table_raw))
        game_table = GamesTable(game_table_raw)
        game_table.print()
        #assert False, f"No check developped!"

        