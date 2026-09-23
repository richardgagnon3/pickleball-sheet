"""Toplevel dialogs for editing a single player cell or a whole team across all games."""

import tkinter as tk
from tkinter import ttk
import logging

_logger = logging.getLogger("__main__")


def _center_dialog(dialog: tk.Toplevel) -> None:
    dialog.update_idletasks()
    x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
    y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
    dialog.geometry(f"+{x}+{y}")


def open_player_cell_dialog(root, games_data: list, game_idx: int, court_name: str | None,
                             row_type: str, current_value: str, player_idx: int, on_save) -> None:
    """Open a dialog to edit a single player's assignment. on_save(new_value: str) applies it."""
    dialog = tk.Toplevel(root)
    dialog.title("Edit Player Assignment")
    dialog.geometry("350x250")
    dialog.transient(root)
    _center_dialog(dialog)

    game_name = games_data[game_idx].get('Game', f'Game {game_idx + 1}')
    ttk.Label(dialog, text=f"Game: {game_name}").pack(pady=5)

    if court_name:
        ttk.Label(dialog, text=f"Court: {court_name}").pack(pady=5)

    if row_type == 'team1':
        ttk.Label(dialog, text=f"Position: Team 1 - Player {player_idx + 1}").pack(pady=5)
        ttk.Label(dialog, text="Enter player number:").pack(pady=5)
    elif row_type == 'team2':
        ttk.Label(dialog, text=f"Position: Team 2 - Player {player_idx + 1}").pack(pady=5)
        ttk.Label(dialog, text="Enter player number:").pack(pady=5)
    elif row_type == 'bench_row':
        ttk.Label(dialog, text=f"Position: Bench {player_idx + 1}").pack(pady=5)
        ttk.Label(dialog, text="Enter bench player number:").pack(pady=5)

    entry = ttk.Entry(dialog, width=30)
    entry.pack(pady=10)
    if current_value:
        entry.insert(0, str(current_value))
    entry.focus()
    entry.select_range(0, tk.END)

    def save_value():
        on_save(entry.get().strip())
        dialog.destroy()

    def cancel():
        dialog.destroy()

    button_frame = ttk.Frame(dialog)
    button_frame.pack(pady=15)
    ttk.Button(button_frame, text="Save", command=save_value).pack(side=tk.LEFT, padx=5)
    ttk.Button(button_frame, text="Cancel", command=cancel).pack(side=tk.LEFT, padx=5)

    dialog.bind('<Return>', lambda e: save_value())
    dialog.bind('<Escape>', lambda e: cancel())

    # Set grab AFTER all widgets are created and dialog is visible
    dialog.after_idle(dialog.grab_set)


def open_team_all_games_dialog(root, games_data: list, row_type: str, court_name: str | None, on_save) -> None:
    """Open a dialog to bulk-edit one team's players across every game. on_save() is called
    (no arguments) after games_data has been mutated in place."""
    dialog = tk.Toplevel(root)
    dialog.title("Edit Team for All Games")
    dialog.geometry("400x300")
    dialog.transient(root)
    _center_dialog(dialog)

    team_name = "Team 1" if row_type == 'team1' else "Team 2"
    ttk.Label(dialog, text=f"Edit {team_name} for Court: {court_name or 'Unknown'}",
             font=("Arial", 12, "bold")).pack(pady=10)

    ttk.Label(dialog, text="Enter player pairs for each game:", font=("Arial", 10)).pack(pady=5)
    ttk.Label(dialog, text="Format: game1_player1,game1_player2;game2_player1,game2_player2;...",
             font=("Arial", 8), wraplength=350).pack(pady=5)

    team_key = 'Team1' if row_type == 'team1' else 'Team2'
    current_assignments = []
    for game in games_data:
        if court_name and court_name in game:
            team_players = game[court_name].get(team_key, [])
            assignment = ','.join(str(p) for p in team_players if p)
        else:
            assignment = ''
        current_assignments.append(assignment)

    text_frame = ttk.Frame(dialog)
    text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    text_widget = tk.Text(text_frame, height=8, width=45, wrap=tk.WORD)
    scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
    text_widget.configure(yscrollcommand=scrollbar.set)

    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    text_widget.insert('1.0', ';'.join(current_assignments))
    text_widget.focus()

    def save_values():
        new_text = text_widget.get('1.0', tk.END).strip()
        new_assignments = new_text.split(';') if new_text else []

        while len(new_assignments) < len(games_data):
            new_assignments.append('')

        for game_idx, assignment in enumerate(new_assignments[:len(games_data)]):
            if court_name and court_name in games_data[game_idx]:
                if assignment.strip():
                    players = [p.strip() for p in assignment.split(',') if p.strip()]
                    games_data[game_idx][court_name][team_key] = players
                else:
                    games_data[game_idx][court_name][team_key] = []

        on_save()
        dialog.destroy()

    def cancel():
        dialog.destroy()

    button_frame = ttk.Frame(dialog)
    button_frame.pack(pady=10)
    ttk.Button(button_frame, text="Save All", command=save_values).pack(side=tk.LEFT, padx=5)
    ttk.Button(button_frame, text="Cancel", command=cancel).pack(side=tk.LEFT, padx=5)

    dialog.bind('<Escape>', lambda e: cancel())

    # Set grab AFTER all widgets are created and dialog is visible
    dialog.after_idle(dialog.grab_set)
