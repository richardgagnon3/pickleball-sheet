"""
Sheet Editor GUI for Pickleball Game Management

This module provides a GUI interface for editing pickleball game sheets.
It allows users to load CSV files, view player assignments in a table format,
and modify player assignments for each game.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import logging

from sheet_reader import SheetReader
from games_table import GamesTable
from game_data_io import read_csv_rows, write_csv_rows, games_to_csv_rows
from game_table_view import GameTableView
from statistics_panel import StatisticsPanel
from cell_selection import CellSelectionController
from invalid_cell_overlay import InvalidCellOverlay
from player_edit_dialogs import open_player_cell_dialog, open_team_all_games_dialog

_logger = logging.getLogger("__main__")

# Repo root, two levels up from src/gui/
_REPO_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")


class SheetEditorGUI:
    """GUI application for editing pickleball game sheets."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Pickleball Sheet Editor")
        self.root.geometry("1000x600")

        # Data storage
        self.current_file = None
        self.csv_data = []  # Raw CSV data for saving
        self.original_data = []  # Original CSV backup
        self.games_data = []  # Parsed game data from SheetReader

        # Setup GUI components
        self.setup_menu()
        self.setup_main_frame()
        self.setup_table()
        self.setup_statistics_panel()

        _logger.debug("SheetEditorGUI initialized")

    def setup_menu(self):
        """Setup the menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open...", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="Save", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="Save As...", command=self.save_as_file, accelerator="Ctrl+Shift+S")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Bind keyboard shortcuts
        self.root.bind('<Control-o>', lambda e: self.open_file())
        self.root.bind('<Control-s>', lambda e: self.save_file())
        self.root.bind('<Control-Shift-S>', lambda e: self.save_as_file())

    def setup_main_frame(self):
        """Setup the main frame with toolbar and paned window."""
        # Main frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Toolbar frame
        toolbar_frame = ttk.Frame(self.main_frame)
        toolbar_frame.pack(fill=tk.X, pady=(0, 5))

        # File info label
        self.file_label = ttk.Label(toolbar_frame, text="No file loaded", font=("Arial", 10))
        self.file_label.pack(side=tk.LEFT)

        # Buttons
        button_frame = ttk.Frame(toolbar_frame)
        button_frame.pack(side=tk.RIGHT)

        ttk.Button(button_frame, text="Open File", command=self.open_file).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Save", command=self.save_file).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Refresh", command=self.refresh_table).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Swap Players", command=self.swap_selected_players).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Update Stats", command=self.update_statistics).pack(side=tk.LEFT)

        # Create paned window for table and statistics
        self.paned_window = ttk.PanedWindow(self.main_frame, orient=tk.VERTICAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

        # Table frame (top pane)
        self.table_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.table_frame, weight=2)

        # Statistics frame (bottom pane)
        self.stats_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.stats_frame, weight=1)

    def setup_table(self):
        """Setup the data table view, cell-selection controller, and invalid-cell overlay."""
        self.table_view = GameTableView(self.table_frame, self.on_cell_click, self.on_item_double_click)
        self.table_view.pack(fill=tk.BOTH, expand=True)
        self.tree = self.table_view.tree

        # Status bar
        self.status_bar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.invalid_overlay = InvalidCellOverlay(self.tree, on_cell_click=self._handle_cell_selection)
        self.cell_selection = CellSelectionController(
            self.tree,
            games_data_provider=lambda: self.games_data,
            status_callback=lambda text: self.status_bar.config(text=text),
            on_cell_text_changed=self.invalid_overlay.sync_cell_text,
        )
        self.table_view.bind_scroll(lambda first, last: self.invalid_overlay.reposition())

    def setup_statistics_panel(self):
        """Setup the statistics panel."""
        self.stats_panel = StatisticsPanel(self.stats_frame)
        self.stats_panel.pack(fill=tk.BOTH, expand=True)

    def open_file(self):
        """Open and load a CSV file."""
        file_path = filedialog.askopenfilename(
            title="Open CSV File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialdir=os.path.join(_REPO_ROOT, "games")
        )

        if file_path:
            try:
                self.load_csv_file(file_path)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file: {str(e)}")
                _logger.error(f"Failed to load file {file_path}: {str(e)}")

    def load_csv_file(self, file_path: str):
        """Load CSV file and populate the table."""
        self.current_file = file_path

        # Read raw CSV data for saving later
        self.csv_data = read_csv_rows(file_path)
        self.original_data = [row[:] for row in self.csv_data]  # Deep copy

        # Parse the games using SheetReader
        try:
            sheet_reader = SheetReader(file_path)
            self.games_data = sheet_reader.read()

            # Validate before accepting the load
            GamesTable(self.games_data)

        except Exception as e:
            _logger.error("Failed to parse game data: %s", str(e))
            messagebox.showerror("Parse Error", f"Failed to parse game data: {str(e)}")
            return

        # Update UI
        self.file_label.config(text=f"File: {os.path.basename(file_path)}")
        self.populate_table()
        self.calculate_statistics()
        self.status_bar.config(text=f"Loaded {len(self.games_data)} games from {os.path.basename(file_path)}")

        _logger.info("Loaded CSV file: %s", file_path)

    def populate_table(self):
        """Populate the table with parsed game data in detailed layout."""
        if not self.games_data:
            return

        # Clear current cell selection and invalid-cell overlays (rows are about to be recreated)
        self.cell_selection.clear_selection()
        self.invalid_overlay.clear()

        self.table_view.populate(self.games_data)

        # Highlight any player cells that currently break table validation
        self.invalid_overlay.refresh(self.games_data)

    def calculate_statistics(self):
        """Recalculate statistics from the current in-memory games_data."""
        self.stats_panel.refresh(self.games_data, self.current_file)

    def update_statistics(self):
        """Update statistics when called from button."""
        self.calculate_statistics()
        self.status_bar.config(text="Statistics updated")

    def on_cell_click(self, event):
        """Handle single click to select up to 2 individual player cells for swapping."""
        item = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)
        return self._handle_cell_selection(item, column)

    def _handle_cell_selection(self, item, column):
        return self.cell_selection.handle_cell_selection(item, column)

    def swap_selected_players(self):
        """Swap the player values of the 2 currently selected cells.

        The swap is always applied, even if it makes the table temporarily invalid
        (e.g. duplicate players in a game); affected cells are then highlighted in red
        so further swaps remain possible.
        """
        result = self.cell_selection.swap_selected()
        if result is None:
            messagebox.showwarning("Warning", "Select exactly 2 player cells to swap.")
            return

        value_a, value_b = result
        self.populate_table()
        self.update_csv_from_games()
        self.calculate_statistics()

        self.status_bar.config(text=f"Swapped players '{value_a}' and '{value_b}'")

    def on_item_double_click(self, event):
        """Handle double-click on table item for editing."""
        item = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)

        if not item or not column:
            return

        col_index = int(column.replace('#', '')) - 1

        # Get item tags to determine what type of row this is
        tags = self.tree.item(item)['tags']
        if not tags:
            return

        row_type = tags[0]

        # Only allow editing team and bench rows
        if row_type in ['team1', 'team2', 'bench_row']:
            # For team rows, allow editing Team column (index 1) and game columns (index >= 2)
            # For bench rows, only allow editing game columns (index >= 2)
            if row_type in ['team1', 'team2'] and col_index == 1:
                # Editing the Team column - allow changing the entire team for all games
                court_name = tags[1] if len(tags) > 1 else None
                open_team_all_games_dialog(self.root, self.games_data, row_type, court_name,
                                            on_save=self._on_team_all_games_saved)
                return
            elif col_index <= 1:  # Don't edit Court column (index 0) or Team column for bench
                return

            current_value = self.tree.item(item)['values'][col_index] if col_index < len(self.tree.item(item)['values']) else ''

            # Determine game index from column (subtract 2 for Court and Team columns)
            game_idx = col_index - 2
            if game_idx >= len(self.games_data):
                return

            # Get court name if it's a team row
            court_name = None
            if len(tags) > 1 and row_type in ['team1', 'team2']:
                court_name = tags[1]

            # Player position within the team/bench, encoded in the row's third tag
            player_idx = int(tags[2]) if len(tags) > 2 else 0

            cell_info = {
                'game_idx': game_idx, 'row_type': row_type, 'court_name': court_name, 'player_idx': player_idx,
            }

            def on_save(new_value: str) -> None:
                self.cell_selection.set_cell_player_value(cell_info, new_value)
                self.populate_table()
                self.update_csv_from_games()
                self.calculate_statistics()
                self.status_bar.config(text=f"Updated {row_type} in Game {game_idx + 1} to '{new_value}'")

            open_player_cell_dialog(self.root, self.games_data, game_idx, court_name, row_type,
                                     current_value, player_idx, on_save)

    def _on_team_all_games_saved(self):
        """Refresh the app after a bulk team-for-all-games edit."""
        self.populate_table()
        self.update_csv_from_games()
        self.calculate_statistics()
        self.status_bar.config(text="Updated team for all games")

    def update_csv_from_games(self):
        """Rebuild self.csv_data from self.games_data, matching the format read by SheetReader."""
        self.csv_data = games_to_csv_rows(self.games_data)

    def save_file(self):
        """Save current data to file."""
        if not self.current_file:
            self.save_as_file()
            return

        try:
            write_csv_rows(self.current_file, self.csv_data)

            self.status_bar.config(text=f"Saved to {os.path.basename(self.current_file)}")
            messagebox.showinfo("Success", f"File saved successfully!")
            _logger.info(f"Saved file: {self.current_file}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file: {str(e)}")
            _logger.error(f"Failed to save file {self.current_file}: {str(e)}")

    def save_as_file(self):
        """Save current data to a new file."""
        if not self.csv_data:
            messagebox.showwarning("Warning", "No data to save!")
            return

        file_path = filedialog.asksaveasfilename(
            title="Save CSV File",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )

        if file_path:
            try:
                write_csv_rows(file_path, self.csv_data)

                self.current_file = file_path
                self.file_label.config(text=f"File: {os.path.basename(file_path)}")
                self.status_bar.config(text=f"Saved to {os.path.basename(file_path)}")
                messagebox.showinfo("Success", f"File saved successfully!")
                _logger.info(f"Saved file as: {file_path}")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {str(e)}")
                _logger.error(f"Failed to save file {file_path}: {str(e)}")

    def refresh_table(self):
        """Refresh the table display."""
        if self.current_file:
            try:
                self.load_csv_file(self.current_file)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to refresh: {str(e)}")
        else:
            messagebox.showwarning("Warning", "No file loaded to refresh!")


def main():
    """Main function to run the application."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create and run GUI
    root = tk.Tk()
    app = SheetEditorGUI(root)

    # Load default file if available
    games_dir = os.path.join(_REPO_ROOT, "games")
    if os.path.exists(games_dir):
        csv_files = [f for f in os.listdir(games_dir) if f.endswith('.csv')]
        if csv_files:
            default_file = os.path.join(games_dir, csv_files[0])
            try:
                app.load_csv_file(default_file)
            except Exception as e:
                _logger.warning(f"Could not load default file {default_file}: {str(e)}")

    root.mainloop()


if __name__ == "__main__":
    main()
