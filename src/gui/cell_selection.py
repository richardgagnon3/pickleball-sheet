"""Player cell selection and swap logic for the sheet editor Treeview."""

import logging

_logger = logging.getLogger("__main__")


class CellSelectionController:
    """Tracks up to 2 selected player cells in the Treeview and supports swapping them."""

    def __init__(self, tree, games_data_provider, status_callback, on_cell_text_changed=None):
        """
        tree: the ttk.Treeview showing player cells.
        games_data_provider: callable returning the current games_data list.
        status_callback: callable(text) to update a status bar.
        on_cell_text_changed: optional callable(item, column) fired whenever a cell's
            displayed text changes (e.g. so an invalid-cell overlay can stay in sync).
        """
        self.tree = tree
        self._games_data_provider = games_data_provider
        self._status_callback = status_callback
        self._on_cell_text_changed = on_cell_text_changed
        self.selected_cells = []

    @property
    def games_data(self) -> list:
        return self._games_data_provider()

    def handle_cell_selection(self, item, column):
        """Select or deselect a player cell (identified by tree item and column) for swapping."""
        if not item or not column:
            return "break"

        col_index = int(column.replace('#', '')) - 1
        tags = list(self.tree.item(item, 'tags'))
        row_type = tags[0] if tags else None

        # Only individual player cells (game columns) can be selected for swapping
        if row_type not in ('team1', 'team2', 'bench_row') or col_index < 2:
            self.clear_selection()
            return "break"

        game_idx = col_index - 2
        if game_idx >= len(self.games_data):
            return "break"

        court_name = tags[1] if row_type in ('team1', 'team2') and len(tags) > 1 else None
        player_idx = int(tags[2]) if len(tags) > 2 else 0

        # Clicking an already-selected cell deselects it
        for i, existing in enumerate(self.selected_cells):
            if existing['item'] == item and existing['col_index'] == col_index:
                self._unmark_cell(existing)
                self.selected_cells.pop(i)
                self._update_status()
                return "break"

        # Keep only the 2 most recent selections
        if len(self.selected_cells) >= 2:
            oldest = self.selected_cells.pop(0)
            self._unmark_cell(oldest)

        cell_info = {
            'item': item, 'column': column, 'col_index': col_index,
            'row_type': row_type, 'court_name': court_name,
            'player_idx': player_idx, 'game_idx': game_idx,
        }
        self._mark_cell(cell_info)
        self.selected_cells.append(cell_info)

        self._update_status()

        _logger.debug("Selected cell: item=%s, column=%s, col_index=%d", item, column, col_index)

        # Prevent Treeview's built-in row-selection binding from graying out the row
        return "break"

    def _update_status(self) -> None:
        """Update the status bar to reflect the current cell selection for swapping."""
        if not self.selected_cells:
            self._status_callback("Ready")
        elif len(self.selected_cells) == 1:
            cell = self.selected_cells[0]
            col_name = self.tree.heading(cell['column'], 'text')
            row_values = self.tree.item(cell['item'], 'values')
            row_label = row_values[1] if len(row_values) > 1 else ''
            self._status_callback(f"Selected: {row_label} in {col_name}. Select a second cell to swap.")
        else:
            self._status_callback("2 cells selected. Click 'Swap Players' to switch them.")

    def clear_selection(self) -> None:
        """Clear the current cell selection."""
        for cell in self.selected_cells:
            self._unmark_cell(cell)

        self.selected_cells = []
        self._status_callback("Ready")

    def _mark_cell(self, cell_info: dict) -> None:
        """Bracket a cell's displayed value so it stays visible regardless of row color."""
        if not self.tree.exists(cell_info['item']):
            return
        value = self.tree.set(cell_info['item'], cell_info['column'])
        cell_info['original_display'] = value
        self.tree.set(cell_info['item'], cell_info['column'], f"[{value}]")
        if self._on_cell_text_changed:
            self._on_cell_text_changed(cell_info['item'], cell_info['column'])

    def _unmark_cell(self, cell_info: dict) -> None:
        """Restore a cell's displayed value after it is deselected."""
        if self.tree.exists(cell_info['item']) and 'original_display' in cell_info:
            self.tree.set(cell_info['item'], cell_info['column'], cell_info['original_display'])
            if self._on_cell_text_changed:
                self._on_cell_text_changed(cell_info['item'], cell_info['column'])

    def _get_player_list(self, cell_info: dict) -> list:
        """Return the mutable player list referenced by a selected cell, padded to its index."""
        game = self.games_data[cell_info['game_idx']]
        if cell_info['row_type'] == 'bench_row':
            players = game.setdefault('Bench', [])
        else:
            court_name = cell_info['court_name']
            court_data = game.setdefault(court_name, {'Team1': [], 'Team2': []})
            team_key = 'Team1' if cell_info['row_type'] == 'team1' else 'Team2'
            players = court_data.setdefault(team_key, [])

        while len(players) <= cell_info['player_idx']:
            players.append('')
        return players

    def get_cell_player_value(self, cell_info: dict) -> str:
        """Return the current player value for a selected cell."""
        return self._get_player_list(cell_info)[cell_info['player_idx']]

    def set_cell_player_value(self, cell_info: dict, value: str) -> None:
        """Set the player value for a cell in the underlying game data."""
        self._get_player_list(cell_info)[cell_info['player_idx']] = value

    def swap_selected(self):
        """Swap the player values of the 2 currently selected cells.

        Always applies the swap, even if it makes the table temporarily invalid (e.g.
        duplicate players in a game); the caller is responsible for refreshing the table,
        CSV data, and statistics, and for highlighting any resulting invalid cells.

        Returns (value_a, value_b) on success, or None if exactly 2 cells weren't selected.
        """
        if len(self.selected_cells) != 2:
            return None

        cell_a, cell_b = self.selected_cells
        self.clear_selection()

        value_a = self.get_cell_player_value(cell_a)
        value_b = self.get_cell_player_value(cell_b)

        self.set_cell_player_value(cell_a, value_b)
        self.set_cell_player_value(cell_b, value_a)

        _logger.debug("Swapped players '%s' and '%s'", value_a, value_b)
        return value_a, value_b
