import pytest
from sheet_score import _excess, score_sheet


def game(name, courts, bench=()):
    """courts: list of ((a, b), (c, d)) team tuples."""
    g = {"Game": name}
    for i, (t1, t2) in enumerate(courts, 1):
        g[f"Terrain {i}"] = {"Team1": list(t1), "Team2": list(t2)}
    if bench:
        g["Bench"] = list(bench)
    return g


class TestExcess:
    def test_even_distribution_is_zero(self):
        assert _excess([3, 3, 3]) == 0

    def test_unavoidable_imbalance_is_zero(self):
        # 10 split over 3 slots can't be better than 3,3,4
        assert _excess([4, 3, 3]) == 0

    def test_one_unit_misplaced(self):
        # 5,3,3 could be 4,4,3: one unit moved
        assert _excess([5, 3, 3]) == 1

    def test_missing_slots_count_as_zero(self):
        # 2 meetings for one pair while 2 other pairs never met
        assert _excess([2], total=2, nb_slots=3) == 1


class TestScoreSheet:
    # 5 players, 1 court, 5 games: each plays 4 games, rests once.
    PERFECT_5 = [
        game("1", [(("1", "2"), ("3", "4"))], bench=["5"]),
        game("2", [(("1", "3"), ("2", "5"))], bench=["4"]),
        game("3", [(("1", "4"), ("3", "5"))], bench=["2"]),
        game("4", [(("1", "5"), ("2", "4"))], bench=["3"]),
        game("5", [(("2", "3"), ("4", "5"))], bench=["1"]),
    ]

    def test_perfect_partners_and_games(self):
        score = score_sheet(self.PERFECT_5)
        assert score.games == 0
        assert score.pauses == 0
        assert score.partners == 0  # 10 partnerships, 10 different pairs

    def test_unequal_games_penalized(self):
        sheet = [dict(g) for g in self.PERFECT_5]
        # Player 5 rests twice, player 4 never rests.
        sheet[1] = game("2", [(("1", "3"), ("2", "4"))], bench=["5"])
        score = score_sheet(sheet)
        assert score.games == 1
        assert score.total >= 100000

    def test_back_to_back_pause_penalized(self):
        sheet = [
            game("1", [(("1", "2"), ("3", "4"))], bench=["5", "6"]),
            game("2", [(("1", "2"), ("3", "4"))], bench=["5", "6"]),
            game("3", [(("5", "6"), ("3", "4"))], bench=["1", "2"]),
            game("4", [(("5", "6"), ("1", "2"))], bench=["3", "4"]),
        ]
        score = score_sheet(sheet)
        assert score.back_to_back_pauses == ["5", "6"]
        assert score.pauses >= 2

    @staticmethod
    def _six_players(benches):
        """1-court sheet for 6 players with the given benches (teams don't matter)."""
        sheet = []
        for i, bench in enumerate(benches, 1):
            on_court = [p for p in "123456" if p not in bench]
            sheet.append(game(str(i), [(on_court[:2], on_court[2:])], bench=bench))
        return sheet

    def test_pause_irregularity_within_tolerance_is_free(self):
        # 6 players, 2 benched: ideal is 2 games between pauses, 1 to 3 accepted.
        sheet = self._six_players([["1", "2"], ["3", "4"], ["1", "5"], ["2", "6"],
                                   ["3", "5"], ["4", "6"], ["1", "2"]])
        score = score_sheet(sheet)
        assert score.pause_range == (1, 3)
        assert score.gaps_per_player["1"] == [1, 3]
        assert score.pauses == 0

    def test_pause_irregularity_beyond_tolerance_penalized(self):
        # Player 5 plays 4 games between pauses (accepted max 3): costs 1.
        sheet = self._six_players([["5", "6"], ["1", "2"], ["3", "4"], ["1", "6"],
                                   ["2", "3"], ["4", "5"]])
        score = score_sheet(sheet)
        assert score.gaps_per_player["5"] == [4]
        assert score.pauses == 1

    def test_repeated_partners_penalized(self):
        sheet = [
            game("1", [(("1", "2"), ("3", "4"))]),
            game("2", [(("1", "2"), ("3", "4"))]),
        ]
        score = score_sheet(sheet)
        # 4 partnerships over 6 possible pairs, but only 2 pairs used twice
        assert score.partners == 2
        # 8 meetings over 6 pairs: best is 1,1,1,1,2,2 ; actual is 2,2,2,2,0,0
        assert score.opponents == 2

    def test_priority_order(self):
        # One unit of a higher-priority criterion outweighs one of the next.
        score = score_sheet(self.PERFECT_5)
        w = score.weights
        assert w["games"] > w["pauses"] > w["bench"] > w["partners"] > w["opponents"]

    def test_repeated_bench_mates_penalized(self):
        # 6 players, 2 benched per game. Players 5 and 6 rest together twice
        # while the 15 possible bench pairs could all be different.
        sheet = [
            game("1", [(("1", "2"), ("3", "4"))], bench=["5", "6"]),
            game("2", [(("1", "5"), ("3", "6"))], bench=["2", "4"]),
            game("3", [(("1", "2"), ("3", "4"))], bench=["5", "6"]),
        ]
        score = score_sheet(sheet)
        assert score.bench_counts[("5", "6")] == 2
        assert score.bench == 1

    def test_different_bench_mates_not_penalized(self):
        sheet = [
            game("1", [(("1", "2"), ("3", "4"))], bench=["5", "6"]),
            game("2", [(("1", "5"), ("2", "6"))], bench=["3", "4"]),
            game("3", [(("3", "5"), ("4", "6"))], bench=["1", "2"]),
        ]
        assert score_sheet(sheet).bench == 0

    def test_single_bench_player_has_no_bench_mates(self):
        assert score_sheet(self.PERFECT_5).bench == 0

    def test_custom_weights(self):
        sheet = [
            game("1", [(("1", "2"), ("3", "4"))]),
            game("2", [(("1", "2"), ("3", "4"))]),
        ]
        score = score_sheet(sheet, weights={"partners": 0, "opponents": 0})
        assert score.total == 0

    def test_empty_sheet(self):
        assert score_sheet([]).total == 0
