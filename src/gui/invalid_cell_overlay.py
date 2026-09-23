"""Red overlay labels marking player cells that break table validation."""

import tkinter as tk
import logging

from game_validation import find_invalid_cells

_logger = logging.getLogger("__main__")


class InvalidCellOverlay:
    """Manages small red Label widgets placed on top of invalid player cells."""

    def __init__(self, tree, on_cell_click):
        """
        tree: the ttk.Treeview showing player cells.
        on_cell_click: callable(item, column) forwarded when an overlay label is clicked,
            so invalid cells remain selectable/swappable.
        """
        self.tree = tree
        self._on_cell_click = on_cell_click
        self.overlays = []

    def clear(self) -> None:
        """Remove all red overlay labels."""
        for overlay in self.overlays:
            overlay['label'].destroy()
        self.overlays = []

    def refresh(self, games_data: list) -> None:
        """Recompute and redraw red highlights for any player cell breaking validation."""
        self.clear()
        for cell_info in find_invalid_cells(games_data):
            self._mark_invalid_cell(cell_info)

    def reposition(self) -> None:
        """Recompute overlay positions, e.g. after the table is scrolled."""
        for overlay in self.overlays:
            self._position_overlay(overlay['label'], overlay['item'], overlay['column'])

    def sync_cell_text(self, item, column: str) -> None:
        """Keep an overlay's text in sync with the underlying cell value (e.g. selection brackets)."""
        for overlay in self.overlays:
            if overlay['item'] == item and overlay['column'] == column:
                overlay['label'].config(text=self.tree.set(item, column))

    def _position_overlay(self, label: tk.Label, item, column: str) -> None:
        """Place (or hide, if scrolled out of view) an overlay label over a specific cell."""
        bbox = self.tree.bbox(item, column)
        if not bbox:
            label.place_forget()
            return
        x, y, width, height = bbox
        label.place(in_=self.tree, x=x, y=y, width=width, height=height)

    def _find_cell_item(self, cell_info: dict):
        """Locate the current tree item matching a cell's row_type/court_name/player_idx."""
        for item in self.tree.get_children():
            tags = self.tree.item(item, 'tags')
            if not tags or tags[0] != cell_info['row_type'] or len(tags) < 3:
                continue
            if cell_info['row_type'] in ('team1', 'team2') and tags[1] != cell_info['court_name']:
                continue
            if tags[2] == str(cell_info['player_idx']):
                return item
        return None

    def _mark_invalid_cell(self, cell_info: dict) -> None:
        """Overlay a red label on top of a player cell that breaks table validation."""
        item = self._find_cell_item(cell_info)
        if item is None:
            return
        column = f"#{cell_info['col_index'] + 1}"
        value = self.tree.set(item, column)

        label = tk.Label(self.tree, text=value, background='#d9534f', foreground='white', anchor='w')
        label.bind('<Button-1>', lambda e, it=item, col=column: self._on_cell_click(it, col))
        self.overlays.append({'label': label, 'item': item, 'column': column})
        self._position_overlay(label, item, column)
