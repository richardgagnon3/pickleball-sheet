"""Pure logic for detecting player cells that break game-table validation (no tkinter)."""

import logging

_logger = logging.getLogger("__main__")


def get_master_players(games_data: list) -> set:
    """Return the set of player values expected to appear in every game (from the first game)."""
    if not games_data:
        return set()
    players = []
    for court, data in games_data[0].items():
        if court == 'Game':
            continue
        if court == 'Bench':
            players += data
        else:
            players += data.get('Team1', [])
            players += data.get('Team2', [])
    return set(p for p in players if p)


def find_invalid_cells(games_data: list) -> list:
    """Return a list of cells (dicts) whose player value is duplicated or foreign within its game.

    Each returned dict has keys: game_idx, row_type ('team1'/'team2'/'bench_row'),
    court_name (None for bench), player_idx, col_index.
    """
    if not games_data:
        return []

    master_players = get_master_players(games_data)
    invalid_cells = []

    for game_idx, game in enumerate(games_data):
        entries = []  # (row_type, court_name, player_idx, value)
        for court, data in game.items():
            if court == 'Game':
                continue
            if court == 'Bench':
                entries += [('bench_row', None, idx, value) for idx, value in enumerate(data) if value]
            else:
                for team_num, team_key in ((1, 'Team1'), (2, 'Team2')):
                    entries += [(f'team{team_num}', court, idx, value)
                                for idx, value in enumerate(data.get(team_key, [])) if value]

        value_counts: dict = {}
        for _, _, _, value in entries:
            value_counts[value] = value_counts.get(value, 0) + 1

        for row_type, court_name, player_idx, value in entries:
            if value_counts[value] > 1 or value not in master_players:
                invalid_cells.append({
                    'game_idx': game_idx, 'row_type': row_type,
                    'court_name': court_name, 'player_idx': player_idx,
                    'col_index': game_idx + 2,
                })

    return invalid_cells
