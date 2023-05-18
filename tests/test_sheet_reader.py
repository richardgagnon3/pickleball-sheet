import pytest
from sheet_reader import SheetReader

class TestSheetReader:

    def test_file_does_not_exist(self):
        reader = SheetReader("bad_filename.csv")
        with pytest.raises(FileNotFoundError):
            reader.read()

    def test_read_csv_file(self):
        reader = SheetReader('/'.join(["pickleball-sheet/src" , "14j-3t.csv"]))
        reader.read()

        