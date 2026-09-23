from game_validation import get_master_players, find_invalid_cells


def _make_games_data(team1_p1='1', team2_p1='3'):
    """Two valid games sharing the same 4-player pool across one court."""
    return [
        {
            "Game": "p1",
            "Terrain 1": {"Team1": [team1_p1, '2'], "Team2": [team2_p1, '4']},
        },
        {
            "Game": "p2",
            "Terrain 1": {"Team1": ['1', '2'], "Team2": ['3', '4']},
        },
    ]


class TestGetMasterPlayers:

    def test_empty_games_data(self):
        assert get_master_players([]) == set()

    def test_collects_team_and_bench_players_from_first_game(self):
        games_data = [
            {
                "Game": "p1",
                "Terrain 1": {"Team1": ['1', '2'], "Team2": ['3', '4']},
                "Bench": ['5', '6'],
            },
        ]
        assert get_master_players(games_data) == {'1', '2', '3', '4', '5', '6'}


class TestFindInvalidCells:

    def test_no_invalid_cells_for_valid_table(self):
        games_data = _make_games_data()
        assert find_invalid_cells(games_data) == []

    def test_detects_duplicate_player_within_a_game(self):
        # game0's Team1 P1 duplicates Team2 P1 ('3'), so both cells are flagged; since the
        # master player list comes from game0, '1' no longer appears there and is flagged
        # wherever else it's found (game1's Team1 P1), matching GamesTable's own semantics.
        games_data = _make_games_data(team1_p1='3')

        invalid = find_invalid_cells(games_data)

        assert len(invalid) == 3
        assert {(c['game_idx'], c['row_type'], c['player_idx']) for c in invalid} == {
            (0, 'team1', 0), (0, 'team2', 0), (1, 'team1', 0),
        }

    def test_detects_foreign_player_not_in_master_list(self):
        # game1 has a player ('9') that never appears in game0 (the master list source)
        games_data = _make_games_data()
        games_data[1]["Terrain 1"]["Team1"][0] = '9'

        invalid = find_invalid_cells(games_data)

        assert len(invalid) == 1
        assert invalid[0]['game_idx'] == 1
        assert invalid[0]['row_type'] == 'team1'
        assert invalid[0]['player_idx'] == 0
