"""
Sheet Editor GUI for Pickleball Game Management

This module provides a GUI interface for editing pickleball game sheets.
It allows users to load CSV files, view player assignments in a table format,
and modify player assignments for each game.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
import os
import logging
from typing import List, Dict, Any

from sheet_reader import SheetReader

_logger = logging.getLogger("__main__")


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
        """Setup the main frame with toolbar."""
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
        ttk.Button(button_frame, text="Refresh", command=self.refresh_table).pack(side=tk.LEFT)

    def setup_table(self):
        """Setup the data table with scrollbars."""
        # Create frame for table and scrollbars
        table_frame = ttk.Frame(self.main_frame)
        table_frame.pack(fill=tk.BOTH, expand=True)

        # Create treeview with scrollbars
        self.tree = ttk.Treeview(table_frame, show='headings')

        # Vertical scrollbar
        v_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=v_scrollbar.set)

        # Horizontal scrollbar
        h_scrollbar = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(xscrollcommand=h_scrollbar.set)

        # Pack scrollbars and treeview
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Bind double-click for editing
        self.tree.bind('<Double-1>', self.on_item_double_click)

        # Status bar
        self.status_bar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def open_file(self):
        """Open and load a CSV file."""
        file_path = filedialog.askopenfilename(
            title="Open CSV File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialdir=os.path.join(os.path.dirname(__file__), "..", "games")
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
        with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            self.csv_data = list(reader)
            self.original_data = [row[:] for row in self.csv_data]  # Deep copy

        # Parse the games using SheetReader
        try:
            sheet_reader = SheetReader(file_path)
            self.games_data = sheet_reader.read()
        except Exception as e:
            _logger.error("Failed to parse game data: %s", str(e))
            messagebox.showerror("Parse Error", f"Failed to parse game data: {str(e)}")
            return

        # Update UI
        self.file_label.config(text=f"File: {os.path.basename(file_path)}")
        self.populate_table()
        self.status_bar.config(text=f"Loaded {len(self.games_data)} games from {os.path.basename(file_path)}")

        _logger.info("Loaded CSV file: %s", file_path)

    def populate_table(self):
        """Populate the table with parsed game data."""
        if not self.games_data:
            return

        # Clear existing data
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Setup columns based on game structure
        columns = ['Game', 'Court', 'Team1_P1', 'Team1_P2', 'Team2_P1', 'Team2_P2', 'Bench']
        self.tree['columns'] = columns

        # Configure column headings and widths
        col_widths = {'Game': 80, 'Court': 100, 'Team1_P1': 80, 'Team1_P2': 80, 
                     'Team2_P1': 80, 'Team2_P2': 80, 'Bench': 120}
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=col_widths.get(col, 100), minwidth=60)

        # Insert game data
        for game_idx, game in enumerate(self.games_data):
            game_name = game.get('Game', f'Game {game_idx + 1}')
            
            # Find courts (exclude 'Game' and 'Bench' keys)
            courts = [key for key in game.keys() if key not in ['Game', 'Bench']]
            
            if not courts:
                # No court data, just show game and bench
                bench_players = ', '.join(str(p) for p in game.get('Bench', []))
                row_data = [game_name, '', '', '', '', '', bench_players]
                item = self.tree.insert('', 'end', values=row_data, 
                                      tags=(f'game_{game_idx}', f'court_none'))
            else:
                # Show each court as a separate row
                for court_idx, court_name in enumerate(courts):
                    court_data = game[court_name]
                    
                    # Extract team data
                    team1 = court_data.get('Team1', [])
                    team2 = court_data.get('Team2', [])
                    
                    team1_p1 = str(team1[0]) if len(team1) > 0 else ''
                    team1_p2 = str(team1[1]) if len(team1) > 1 else ''
                    team2_p1 = str(team2[0]) if len(team2) > 0 else ''
                    team2_p2 = str(team2[1]) if len(team2) > 1 else ''
                    
                    # Show bench only for first court row
                    bench_players = ''
                    if court_idx == 0:
                        bench_players = ', '.join(str(p) for p in game.get('Bench', []))
                    
                    row_data = [game_name if court_idx == 0 else '', 
                               court_name, team1_p1, team1_p2, team2_p1, team2_p2, bench_players]
                    
                    item = self.tree.insert('', 'end', values=row_data, 
                                          tags=(f'game_{game_idx}', f'court_{court_name}'))
                    
                    # Add alternating row colors
                    if game_idx % 2 == 0:
                        self.tree.tag_configure(f'game_{game_idx}', background='#f8f8f8')

        _logger.debug("Populated table with %d games", len(self.games_data))
    
    def on_item_double_click(self, event):
        """Handle double-click on table item for editing."""
        if not self.tree.selection():
            return
            
        item = self.tree.selection()[0]
        column = self.tree.identify_column(event.x)

        if column:
            col_index = int(column.replace('#', '')) - 1
            columns = ['Game', 'Court', 'Team1_P1', 'Team1_P2', 'Team2_P1', 'Team2_P2', 'Bench']
            
            # Only allow editing player positions and bench
            if col_index >= 2 and col_index < len(columns):  # Team1_P1, Team1_P2, Team2_P1, Team2_P2, Bench
                column_name = columns[col_index]
                current_value = self.tree.item(item)['values'][col_index] if col_index < len(self.tree.item(item)['values']) else ''
                
                # Get game and court info from tags
                tags = self.tree.item(item)['tags']
                if len(tags) >= 2:
                    game_tag = tags[0]  # format: game_X
                    court_tag = tags[1]  # format: court_Y
                    
                    # Create edit dialog
                    self.edit_player_cell(game_tag, court_tag, column_name, current_value, item, col_index)

    def edit_player_cell(self, game_tag: str, court_tag: str, column_name: str, current_value: str, tree_item, col_index: int):
        """Open dialog to edit player assignment."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Player Assignment")
        dialog.geometry("350x200")
        dialog.transient(self.root)
        dialog.grab_set()

        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        # Extract game index and court name
        game_idx = int(game_tag.split('_')[1])
        court_name = court_tag.replace('court_', '') if court_tag != 'court_none' else None

        ttk.Label(dialog, text=f"Game: {self.games_data[game_idx].get('Game', f'Game {game_idx + 1}')}").pack(pady=5)
        if court_name:
            ttk.Label(dialog, text=f"Court: {court_name}").pack(pady=5)
        ttk.Label(dialog, text=f"Position: {column_name}").pack(pady=5)

        if column_name == 'Bench':
            ttk.Label(dialog, text="Enter player numbers separated by commas:").pack(pady=5)
        else:
            ttk.Label(dialog, text="Enter player number:").pack(pady=5)

        entry = ttk.Entry(dialog, width=30)
        entry.pack(pady=10)
        entry.insert(0, current_value)
        entry.focus()
        entry.select_range(0, tk.END)

        def save_value():
            new_value = entry.get().strip()
            self.update_player_assignment(game_idx, court_name, column_name, new_value, tree_item, col_index)
            dialog.destroy()

        def cancel():
            dialog.destroy()

        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=15)

        ttk.Button(button_frame, text="Save", command=save_value).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=cancel).pack(side=tk.LEFT, padx=5)

        # Bind Enter and Escape keys
        dialog.bind('<Return>', lambda e: save_value())
        dialog.bind('<Escape>', lambda e: cancel())

    def update_player_assignment(self, game_idx: int, court_name: str | None, column_name: str, new_value: str, tree_item, col_index: int):
        """Update player assignment in game data and table."""
        if game_idx >= len(self.games_data):
            _logger.error("Game index %d out of range", game_idx)
            return

        game = self.games_data[game_idx]

        try:
            if column_name == 'Bench':
                # Handle bench players (comma-separated list)
                if new_value.strip():
                    bench_players = [p.strip() for p in new_value.split(',') if p.strip()]
                    game['Bench'] = bench_players
                else:
                    game['Bench'] = []
            else:
                # Handle team player positions
                if not court_name or court_name not in game:
                    _logger.error("Court %s not found in game %d", court_name, game_idx)
                    return

                court_data = game[court_name]
                
                if column_name == 'Team1_P1':
                    if 'Team1' not in court_data:
                        court_data['Team1'] = []
                    while len(court_data['Team1']) < 1:
                        court_data['Team1'].append('')
                    court_data['Team1'][0] = new_value
                elif column_name == 'Team1_P2':
                    if 'Team1' not in court_data:
                        court_data['Team1'] = []
                    while len(court_data['Team1']) < 2:
                        court_data['Team1'].append('')
                    court_data['Team1'][1] = new_value
                elif column_name == 'Team2_P1':
                    if 'Team2' not in court_data:
                        court_data['Team2'] = []
                    while len(court_data['Team2']) < 1:
                        court_data['Team2'].append('')
                    court_data['Team2'][0] = new_value
                elif column_name == 'Team2_P2':
                    if 'Team2' not in court_data:
                        court_data['Team2'] = []
                    while len(court_data['Team2']) < 2:
                        court_data['Team2'].append('')
                    court_data['Team2'][1] = new_value

            # Update table display
            current_values = list(self.tree.item(tree_item)['values'])
            while len(current_values) <= col_index:
                current_values.append('')
            current_values[col_index] = new_value
            self.tree.item(tree_item, values=current_values)

            # Also update the CSV data for saving
            self.update_csv_from_games()

            self.status_bar.config(text=f"Updated {column_name} to '{new_value}'")
            _logger.debug("Updated %s to '%s' in game %d", column_name, new_value, game_idx)

        except Exception as e:
            _logger.error("Failed to update player assignment: %s", str(e))
            messagebox.showerror("Error", f"Failed to update player assignment: {str(e)}")

    def update_csv_from_games(self):
        """Update the CSV data structure from the parsed games data."""
        # This is a simplified approach - we need to reconstruct the CSV format
        # For now, we'll just mark that changes were made
        # TODO: Implement proper CSV reconstruction from games data
        pass

    def save_file(self):
        """Save current data to file."""
        if not self.current_file:
            self.save_as_file()
            return

        try:
            with open(self.current_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerows(self.csv_data)

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
                with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerows(self.csv_data)

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
    games_dir = os.path.join(os.path.dirname(__file__), "..", "games")
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