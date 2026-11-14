import os
import random
import tempfile

import pytest
from game_data_io import games_to_csv_rows, write_csv_rows
from games_table import GamesTable
from sheet_generator import generate_sheet, optimize
from sheet_reader import SheetReader


class TestSheetGenerator:
    @pytest.mark.parametrize("players,courts,games", [(4, 1, 3), (6, 1, 9), (11, 2, 10), (18, 3, 12)])
    def test_generated_sheet_is_valid(self, players, courts, games):
        games_data = generate_sheet(players, courts, games, random.Random(0))
        GamesTable(games_data)  # raises if invalid
        assert len(games_data) == games
        assert len(GamesTable(games_data).get_players_list()) == players

    def test_not_enough_players(self):
        with pytest.raises(ValueError):
            generate_sheet(7, 2, 5, random.Random(0))

    def test_round_trip_through_csv(self):
        games_data = generate_sheet(9, 2, 10, random.Random(0))
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "sheet.csv")
            write_csv_rows(path, games_to_csv_rows(games_data))
            assert SheetReader(path).read() == games_data

    def test_optimize_returns_sorted_best(self):
        results = optimize(6, 1, 9, tries=200, keep=3, seed=1)
        assert len(results) == 3
        totals = [score.total for score, _ in results]
        assert totals == sorted(totals)
        # Balanced pauses are always achievable for 6 players / 9 games.
        assert results[0][0].games == 0
        assert results[0][0].pauses == 0

    def test_seed_is_reproducible(self):
        a = optimize(6, 1, 9, tries=50, keep=1, seed=42)
        b = optimize(6, 1, 9, tries=50, keep=1, seed=42)
        assert a[0][1] == b[0][1]
