"""Treeview widget for displaying game data in the sheet editor."""

import tkinter as tk
from tkinter import ttk
import logging

_logger = logging.getLogger("__main__")


class GameTableView(ttk.Frame):
    """Frame wrapping the games Treeview, its scrollbars, and column/row layout."""

    def __init__(self, parent, on_cell_click, on_cell_double_click):
        super().__init__(parent)

        self.tree = ttk.Treeview(self, show='headings')

        self.v_scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=self._on_yscroll)

        h_scrollbar = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(xscrollcommand=h_scrollbar.set)

        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.tree.bind('<Button-1>', on_cell_click)
        self.tree.bind('<Double-1>', on_cell_double_click)

        # Called after every scroll, so overlays anchored to cells can reposition themselves
        self._on_scroll_callback = None

    def bind_scroll(self, on_scroll_callback) -> None:
        """Register a callback invoked after every vertical scroll (first, last)."""
        self._on_scroll_callback = on_scroll_callback

    def _on_yscroll(self, first, last) -> None:
        self.v_scrollbar.set(first, last)
        if self._on_scroll_callback:
            self._on_scroll_callback(first, last)

    def clear(self) -> None:
        """Remove all rows from the table."""
        for item in self.tree.get_children():
            self.tree.delete(item)

    def populate(self, games_data: list) -> None:
        """Populate the table with parsed game data in detailed layout."""
        self.clear()

        if not games_data:
            return

        # Create dynamic columns based on number of games
        num_games = len(games_data)
        columns = ['Court', 'Team'] + [f'Game_{i+1}' for i in range(num_games)]
        self.tree['columns'] = columns

        # Configure column headings and widths
        self.tree.heading('Court', text='Court')
        self.tree.column('Court', width=100, minwidth=80)
        self.tree.heading('Team', text='Team')
        self.tree.column('Team', width=80, minwidth=60)

        for i in range(num_games):
            game_name = games_data[i].get('Game', f'p{i+1}')
            self.tree.heading(f'Game_{i+1}', text=game_name)
            self.tree.column(f'Game_{i+1}', width=80, minwidth=60, anchor=tk.CENTER)

        # Find all courts across all games
        all_courts = set()
        for game in games_data:
            courts = [key for key in game.keys() if key not in ['Game', 'Bench']]
            all_courts.update(courts)

        all_courts = sorted(list(all_courts))

        # Insert court data with court name in first column, one row per player position
        self.tree.tag_configure('team1', background='#f0f8ff')
        self.tree.tag_configure('team2', background='#ffe4e1')
        self.tree.tag_configure('vs_row', background='#fffacd', font=('Arial', 8, 'italic'))

        for court_name in all_courts:
            for team_num, team_key in ((1, 'Team1'), (2, 'Team2')):
                row_type = f'team{team_num}'
                for player_idx in range(2):
                    row_label = f'Team {team_num} - P{player_idx + 1}'
                    row_data = [court_name if team_num == 1 and player_idx == 0 else '', row_label]
                    for game in games_data:
                        team_players = game.get(court_name, {}).get(team_key, [])
                        value = str(team_players[player_idx]) if player_idx < len(team_players) and team_players[player_idx] else ''
                        row_data.append(value)

                    self.tree.insert('', 'end', values=row_data,
                                    tags=(row_type, court_name, str(player_idx)))

                if team_num == 1:
                    # VS row between teams
                    vs_data = ['', 'vs'] + ['vs'] * num_games
                    self.tree.insert('', 'end', values=vs_data, tags=('vs_row',))

            # Separator
            sep_data = ['', ''] + [''] * num_games
            self.tree.insert('', 'end', values=sep_data, tags=('separator',))

        # Bench section
        bench_header_data = ['BENCH', ''] + [''] * num_games
        self.tree.insert('', 'end', values=bench_header_data, tags=('bench_header',))
        self.tree.tag_configure('bench_header', background='#ffeb9c', font=('Arial', 10, 'bold'))

        # Find maximum bench players across all games
        max_bench = 0
        for game in games_data:
            bench_size = len(game.get('Bench', []))
            max_bench = max(max_bench, bench_size)

        # Create rows for each bench position
        for bench_pos in range(max_bench):
            bench_data = ['', f'Bench {bench_pos + 1}']
            for game in games_data:
                bench_players = game.get('Bench', [])
                if bench_pos < len(bench_players):
                    bench_data.append(str(bench_players[bench_pos]))
                else:
                    bench_data.append('')

            self.tree.insert('', 'end', values=bench_data,
                            tags=('bench_row', '', str(bench_pos)))
            self.tree.tag_configure('bench_row', background='#f5f5dc')

        _logger.debug("Populated table with %d games in detailed layout", len(games_data))
