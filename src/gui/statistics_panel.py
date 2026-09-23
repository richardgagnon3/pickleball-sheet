"""Statistics notebook (Player Statistics / Overall Statistics / Errors tabs)."""

import os
import tkinter as tk
from tkinter import ttk
import logging
import pandas as pd

from games_table import GamesTable
from player import Player, PlayerStatistics

_logger = logging.getLogger("__main__")


class StatisticsPanel(ttk.Frame):
    """Frame owning the Player Statistics / Overall Statistics / Errors tabs."""

    def __init__(self, parent):
        super().__init__(parent)

        self.player_stats = {}
        self.overall_stats = None
        self.games_table = None

        self.stats_notebook = ttk.Notebook(self)
        self.stats_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self._setup_player_stats_tab()
        self._setup_overall_stats_tab()
        self._setup_errors_tab()

    def _setup_player_stats_tab(self) -> None:
        self.player_stats_frame = ttk.Frame(self.stats_notebook)
        self.stats_notebook.add(self.player_stats_frame, text="Player Statistics")

        self.player_stats_tree = ttk.Treeview(self.player_stats_frame, show='headings')

        player_columns = ['Player', 'Games', 'Pauses', 'Min Inter-Bench', 'Avg Inter-Bench',
                         'Max Inter-Bench', 'Std Dev', 'Variance']
        self.player_stats_tree['columns'] = player_columns

        for col in player_columns:
            self.player_stats_tree.heading(col, text=col)
            self.player_stats_tree.column(col, width=100, minwidth=80)

        player_v_scroll = ttk.Scrollbar(self.player_stats_frame, orient=tk.VERTICAL,
                                       command=self.player_stats_tree.yview)
        self.player_stats_tree.configure(yscrollcommand=player_v_scroll.set)

        player_h_scroll = ttk.Scrollbar(self.player_stats_frame, orient=tk.HORIZONTAL,
                                       command=self.player_stats_tree.xview)
        self.player_stats_tree.configure(xscrollcommand=player_h_scroll.set)

        player_v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        player_h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.player_stats_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _setup_overall_stats_tab(self) -> None:
        self.overall_stats_frame = ttk.Frame(self.stats_notebook)
        self.stats_notebook.add(self.overall_stats_frame, text="Overall Statistics")

        self.overall_stats_text = tk.Text(self.overall_stats_frame, wrap=tk.WORD, height=8)
        overall_scroll = ttk.Scrollbar(self.overall_stats_frame, orient=tk.VERTICAL,
                                      command=self.overall_stats_text.yview)
        self.overall_stats_text.configure(yscrollcommand=overall_scroll.set)

        overall_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.overall_stats_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _setup_errors_tab(self) -> None:
        self.errors_frame = ttk.Frame(self.stats_notebook)
        self.stats_notebook.add(self.errors_frame, text="Errors")

        self.errors_text = tk.Text(self.errors_frame, wrap=tk.WORD, foreground='#d9534f')
        errors_scroll = ttk.Scrollbar(self.errors_frame, orient=tk.VERTICAL,
                                     command=self.errors_text.yview)
        self.errors_text.configure(yscrollcommand=errors_scroll.set)

        errors_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.errors_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def refresh(self, games_data: list, current_file: str | None = None) -> bool:
        """Recalculate statistics from games_data. Returns True on success, False if invalid.

        On success, the Overall Statistics tab is selected; on failure (e.g. duplicate
        players introduced by a swap), the Errors tab is selected with the validation
        message instead of raising or blocking with a dialog.
        """
        if not games_data:
            return False

        try:
            # Rebuild GamesTable so edits made to games_data are picked up and re-validated
            self.games_table = GamesTable(games_data)

            players_list = self.games_table.get_players_list()
            self.player_stats = {}

            for player_name in players_list:
                player = Player(player_name)
                stats = PlayerStatistics(player)
                stats.analyze_benching(self.games_table)
                self.player_stats[player_name] = stats

            overall_stats_columns = [
                "player", "games", "pauses", "inter_bench_min", "inter_bench_avg",
                "inter_bench_max", "inter_bench_std", "inter_bench_var"
            ]

            stats_data = [stats.toDict() for stats in self.player_stats.values()]

            if stats_data:
                self.overall_stats = pd.DataFrame(stats_data)
                for col in overall_stats_columns:
                    if col not in self.overall_stats.columns:
                        self.overall_stats[col] = 0
            else:
                self.overall_stats = pd.DataFrame(columns=overall_stats_columns)

            self._update_display(current_file)

            self.errors_text.delete('1.0', tk.END)
            self.stats_notebook.select(self.overall_stats_frame)
            return True

        except Exception as e:
            _logger.warning("Skipped statistics update, invalid game data: %s", str(e))
            self.errors_text.delete('1.0', tk.END)
            self.errors_text.insert('1.0', str(e))
            self.stats_notebook.select(self.errors_frame)
            return False

    def _update_display(self, current_file: str | None) -> None:
        """Refresh the Player Statistics and Overall Statistics tab contents."""
        for item in self.player_stats_tree.get_children():
            self.player_stats_tree.delete(item)

        for player_name, stats in self.player_stats.items():
            stats_dict = stats.toDict()
            values = [
                stats_dict.get('player', player_name),
                stats_dict.get('games', 0),
                stats_dict.get('pauses', 0),
                stats_dict.get('inter_bench_min', '-'),
                f"{stats_dict.get('inter_bench_avg', 0):.1f}",
                stats_dict.get('inter_bench_max', '-'),
                f"{stats_dict.get('inter_bench_std', 0):.2f}",
                f"{stats_dict.get('inter_bench_var', 0):.2f}"
            ]
            self.player_stats_tree.insert('', 'end', values=values)

        self.overall_stats_text.delete('1.0', tk.END)

        if self.overall_stats is not None and not self.overall_stats.empty:
            played_games_std = self.overall_stats['games'].std()
            max_games_diff = self.overall_stats['games'].max() - self.overall_stats['games'].min()
            inter_bench_avg_std = self.overall_stats['inter_bench_avg'].std() if 'inter_bench_avg' in self.overall_stats.columns else 0

            stats_text = f"Overall Statistics for {os.path.basename(current_file) if current_file else 'current file'}:\n\n"
            stats_text += f"Played games standard deviation: {played_games_std:.2f}\n"
            stats_text += f"  Difference between max and min played games: {max_games_diff}\n"
            stats_text += f"Inter-bench average standard deviation: {inter_bench_avg_std:.2f}\n"

            if 'inter_bench_min' in self.overall_stats.columns and 'inter_bench_max' in self.overall_stats.columns:
                min_inter_bench = self.overall_stats['inter_bench_min'].min()
                max_inter_bench = self.overall_stats['inter_bench_max'].max()
                stats_text += f"  Inter-bench range: {min_inter_bench} - {max_inter_bench}\n"

                if max_games_diff > 1:
                    stats_text += f"\n⚠️  WARNING: Max-min game difference > 1 ({max_games_diff})\n"

                if min_inter_bench == 0:
                    benched_twice_players = self.overall_stats[self.overall_stats['inter_bench_min'] == 0]['player'].tolist()
                    stats_text += f"\n⚠️  WARNING: Players benched twice in a row: {', '.join(benched_twice_players)}\n"

                if min_inter_bench != max_inter_bench:
                    quick_benched = self.overall_stats[self.overall_stats['inter_bench_min'] == min_inter_bench]['player'].tolist()
                    stats_text += f"\nPlayers with lowest inter-bench time: {', '.join(quick_benched)}\n"

            self.overall_stats_text.insert('1.0', stats_text)
        else:
            self.overall_stats_text.insert('1.0', "No statistics available. Please load a CSV file first.")
