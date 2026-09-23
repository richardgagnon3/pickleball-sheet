"""CSV I/O helpers for reading and reconstructing games_data (as parsed by SheetReader)."""

import csv
import logging

_logger = logging.getLogger("__main__")


def read_csv_rows(file_path: str) -> list:
    """Read a CSV file into a list of raw rows."""
    with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
        return list(csv.reader(csvfile))


def write_csv_rows(file_path: str, rows: list) -> None:
    """Write raw CSV rows to a file."""
    with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
        csv.writer(csvfile).writerows(rows)


def games_to_csv_rows(games_data: list) -> list:
    """Rebuild raw CSV rows from games_data, matching the format read by SheetReader."""
    if not games_data:
        return []

    num_games = len(games_data)
    game_tags = [game.get('Game', '') for game in games_data]
    rows = [game_tags]

    # Court names are every key except 'Game' and 'Bench', in insertion order
    court_names = [key for key in games_data[0].keys() if key not in ('Game', 'Bench')]

    for court_name in court_names:
        rows.append([court_name] + [''] * (num_games - 1))
        for team_key in ('Team1', 'Team2'):
            for player_idx in range(2):
                row = []
                for game in games_data:
                    team = game.get(court_name, {}).get(team_key, [])
                    row.append(team[player_idx] if player_idx < len(team) else '')
                rows.append(row)

    max_bench = max((len(game.get('Bench', [])) for game in games_data), default=0)
    if max_bench > 0:
        rows.append(['Pause'] + [''] * (num_games - 1))
        for bench_idx in range(max_bench):
            row = [game.get('Bench', [])[bench_idx] if bench_idx < len(game.get('Bench', [])) else ''
                   for game in games_data]
            rows.append(row)

    return rows
