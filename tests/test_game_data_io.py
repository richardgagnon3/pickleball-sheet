import os
import tempfile

from sheet_reader import SheetReader
from game_data_io import read_csv_rows, write_csv_rows, games_to_csv_rows

GAMES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "games"
)


class TestGameDataIo:

    def test_games_to_csv_rows_empty(self):
        assert games_to_csv_rows([]) == []

    def test_round_trip_matches_original_games_data(self):
        original_file = os.path.join(GAMES_DIR, "06j-1t.csv")
        games_data = SheetReader(original_file).read()

        rows = games_to_csv_rows(games_data)

        with tempfile.TemporaryDirectory() as tmpdir:
            round_trip_file = os.path.join(tmpdir, "round_trip.csv")
            write_csv_rows(round_trip_file, rows)
            round_trip_games_data = SheetReader(round_trip_file).read()

        assert round_trip_games_data == games_data

    def test_round_trip_reflects_in_memory_edit(self):
        original_file = os.path.join(GAMES_DIR, "06j-1t.csv")
        games_data = SheetReader(original_file).read()

        # Swap a bench player with a court player (Bench has no sort invariant to preserve,
        # unlike Team1/Team2 which SheetReader re-sorts by player number on read)
        games_data[0]["Bench"][0], games_data[0]["Terrain 1"]["Team2"][1] = (
            games_data[0]["Terrain 1"]["Team2"][1], games_data[0]["Bench"][0]
        )

        rows = games_to_csv_rows(games_data)

        with tempfile.TemporaryDirectory() as tmpdir:
            round_trip_file = os.path.join(tmpdir, "round_trip.csv")
            write_csv_rows(round_trip_file, rows)
            round_trip_games_data = SheetReader(round_trip_file).read()

        assert round_trip_games_data == games_data

    def test_read_csv_rows_matches_raw_csv_reader(self):
        original_file = os.path.join(GAMES_DIR, "06j-1t.csv")
        rows = read_csv_rows(original_file)
        assert rows[0][0] == "p1"
