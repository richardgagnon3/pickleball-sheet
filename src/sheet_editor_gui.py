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
        """Populate the table with parsed game data in detailed layout."""
        if not self.games_data:
            return

        # Clear existing data
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Create dynamic columns based on number of games
        num_games = len(self.games_data)
        columns = ['Court_Team'] + [f'Game_{i+1}' for i in range(num_games)]
        self.tree['columns'] = columns

        # Configure column headings and widths
        self.tree.heading('Court_Team', text='Court/Team')
        self.tree.column('Court_Team', width=120, minwidth=100)
        
        for i in range(num_games):
            game_name = self.games_data[i].get('Game', f'p{i+1}')
            self.tree.heading(f'Game_{i+1}', text=game_name)
            self.tree.column(f'Game_{i+1}', width=80, minwidth=60)

        # Find all courts across all games
        all_courts = set()
        for game in self.games_data:
            courts = [key for key in game.keys() if key not in ['Game', 'Bench']]
            all_courts.update(courts)
        
        all_courts = sorted(list(all_courts))

        # Insert court data
        for court_name in all_courts:
            # Insert court header
            court_header_data = [f"=== {court_name} ==="] + [''] * num_games
            court_item = self.tree.insert('', 'end', values=court_header_data, 
                                        tags=('court_header',))
            self.tree.tag_configure('court_header', background='#e0e0e0', font=('Arial', 10, 'bold'))
            
            # Team 1 row
            team1_data = ['Team 1']
            for game in self.games_data:
                if court_name in game:
                    team1 = game[court_name].get('Team1', [])
                    team1_str = ','.join(str(p) for p in team1 if p)
                else:
                    team1_str = ''
                team1_data.append(team1_str)
            
            team1_item = self.tree.insert('', 'end', values=team1_data, 
                                        tags=('team1', court_name))
            self.tree.tag_configure('team1', background='#f0f8ff')
            
            # VS row
            vs_data = ['   vs'] + ['vs'] * num_games
            vs_item = self.tree.insert('', 'end', values=vs_data, 
                                     tags=('vs_row',))
            self.tree.tag_configure('vs_row', background='#fffacd', font=('Arial', 8, 'italic'))
            
            # Team 2 row  
            team2_data = ['Team 2']
            for game in self.games_data:
                if court_name in game:
                    team2 = game[court_name].get('Team2', [])
                    team2_str = ','.join(str(p) for p in team2 if p)
                else:
                    team2_str = ''
                team2_data.append(team2_str)
            
            team2_item = self.tree.insert('', 'end', values=team2_data, 
                                        tags=('team2', court_name))
            self.tree.tag_configure('team2', background='#ffe4e1')
            
            # Separator
            sep_data = [''] + [''] * num_games
            self.tree.insert('', 'end', values=sep_data, tags=('separator',))

        # Bench section
        bench_header_data = ['=== BENCH ==='] + [''] * num_games
        bench_header_item = self.tree.insert('', 'end', values=bench_header_data, 
                                           tags=('bench_header',))
        self.tree.tag_configure('bench_header', background='#ffeb9c', font=('Arial', 10, 'bold'))
        
        # Find maximum bench players across all games
        max_bench = 0
        for game in self.games_data:
            bench_size = len(game.get('Bench', []))
            max_bench = max(max_bench, bench_size)
        
        # Create rows for each bench position
        for bench_pos in range(max_bench):
            bench_data = [f'Bench {bench_pos + 1}']
            for game in self.games_data:
                bench_players = game.get('Bench', [])
                if bench_pos < len(bench_players):
                    bench_data.append(str(bench_players[bench_pos]))
                else:
                    bench_data.append('')
            
            bench_item = self.tree.insert('', 'end', values=bench_data, 
                                        tags=('bench_row',))
            self.tree.tag_configure('bench_row', background='#f5f5dc')

        _logger.debug("Populated table with %d games in detailed layout", len(self.games_data))
    
    def on_item_double_click(self, event):
        """Handle double-click on table item for editing."""
        if not self.tree.selection():
            return
            
        item = self.tree.selection()[0]
        column = self.tree.identify_column(event.x)

        if column:
            col_index = int(column.replace('#', '')) - 1
            
            # Get item tags to determine what type of row this is
            tags = self.tree.item(item)['tags']
            if not tags:
                return
                
            row_type = tags[0]
            
            # Only allow editing team and bench rows
            if row_type in ['team1', 'team2', 'bench_row']:
                if col_index == 0:  # Don't edit the first column (labels)
                    return
                    
                current_value = self.tree.item(item)['values'][col_index] if col_index < len(self.tree.item(item)['values']) else ''
                
                # Determine game index from column
                game_idx = col_index - 1  # Subtract 1 because first column is labels
                if game_idx >= len(self.games_data):
                    return
                
                # Get court name if it's a team row
                court_name = None
                if len(tags) > 1 and row_type in ['team1', 'team2']:
                    court_name = tags[1]
                
                # Create edit dialog
                self.edit_player_cell_new_layout(game_idx, court_name, row_type, current_value, item, col_index)

    def edit_player_cell_new_layout(self, game_idx: int, court_name: str | None, row_type: str, current_value: str, tree_item, col_index: int):
        """Open dialog to edit player assignment in new layout."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Player Assignment")
        dialog.geometry("350x250")
        dialog.transient(self.root)
        dialog.grab_set()

        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        # Display info
        game_name = self.games_data[game_idx].get('Game', f'Game {game_idx + 1}')
        ttk.Label(dialog, text=f"Game: {game_name}").pack(pady=5)
        
        if court_name:
            ttk.Label(dialog, text=f"Court: {court_name}").pack(pady=5)
        
        if row_type == 'team1':
            ttk.Label(dialog, text="Position: Team 1").pack(pady=5)
            ttk.Label(dialog, text="Enter players separated by commas (e.g., 1,2):").pack(pady=5)
        elif row_type == 'team2':
            ttk.Label(dialog, text="Position: Team 2").pack(pady=5)
            ttk.Label(dialog, text="Enter players separated by commas (e.g., 3,4):").pack(pady=5)
        elif row_type == 'bench_row':
            ttk.Label(dialog, text="Position: Bench").pack(pady=5)
            ttk.Label(dialog, text="Enter bench player number:").pack(pady=5)

        entry = ttk.Entry(dialog, width=30)
        entry.pack(pady=10)
        entry.insert(0, current_value)
        entry.focus()
        entry.select_range(0, tk.END)

        def save_value():
            new_value = entry.get().strip()
            self.update_player_assignment_new_layout(game_idx, court_name, row_type, new_value, tree_item, col_index)
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

    def update_player_assignment_new_layout(self, game_idx: int, court_name: str | None, row_type: str, new_value: str, tree_item, col_index: int):
        """Update player assignment in new layout format."""
        if game_idx >= len(self.games_data):
            _logger.error("Game index %d out of range", game_idx)
            return

        game = self.games_data[game_idx]

        try:
            if row_type == 'bench_row':
                # Handle bench players - find which bench position this is
                bench_players = game.get('Bench', [])
                
                # Get the row label to determine bench position
                current_values = list(self.tree.item(tree_item)['values'])
                row_label = current_values[0] if current_values else ''
                
                if 'Bench' in row_label:
                    # Extract bench position number
                    try:
                        bench_pos = int(row_label.split()[-1]) - 1  # Convert to 0-based index
                    except (ValueError, IndexError):
                        bench_pos = 0
                    
                    # Ensure bench list is long enough
                    while len(bench_players) <= bench_pos:
                        bench_players.append('')
                    
                    if new_value.strip():
                        bench_players[bench_pos] = new_value.strip()
                    else:
                        bench_players[bench_pos] = ''
                    
                    # Remove empty entries from the end
                    while bench_players and bench_players[-1] == '':
                        bench_players.pop()
                    
                    game['Bench'] = bench_players

            elif row_type in ['team1', 'team2'] and court_name:
                # Handle team assignments
                if court_name not in game:
                    game[court_name] = {'Team1': [], 'Team2': []}
                
                court_data = game[court_name]
                team_key = 'Team1' if row_type == 'team1' else 'Team2'
                
                if new_value.strip():
                    # Parse comma-separated players
                    players = [p.strip() for p in new_value.split(',') if p.strip()]
                    court_data[team_key] = players
                else:
                    court_data[team_key] = []

            # Update table display
            current_values = list(self.tree.item(tree_item)['values'])
            while len(current_values) <= col_index:
                current_values.append('')
            current_values[col_index] = new_value
            self.tree.item(tree_item, values=current_values)

            # Update CSV data for saving
            self.update_csv_from_games()

            self.status_bar.config(text=f"Updated {row_type} to '{new_value}'")
            _logger.debug("Updated %s to '%s' in game %d", row_type, new_value, game_idx)

        except Exception as e:
            _logger.error("Failed to update player assignment: %s", str(e))
            messagebox.showerror("Error", f"Failed to update player assignment: {str(e)}")

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