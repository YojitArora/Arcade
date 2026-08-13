"""Small server-authoritative Minesweeper game used by the shared arcade."""

from __future__ import annotations

import random
from dataclasses import dataclass, field


@dataclass
class MinesweeperGame:
    rows: int = 9
    columns: int = 9
    mine_count: int = 10
    mines: set[int] = field(default_factory=set)
    revealed: set[int] = field(default_factory=set)
    flagged: set[int] = field(default_factory=set)
    status: str = "playing"

    def __post_init__(self) -> None:
        self.new_game()

    @property
    def total_cells(self) -> int:
        return self.rows * self.columns

    def new_game(self) -> None:
        self.mines = set(random.sample(range(self.total_cells), self.mine_count))
        self.revealed = set()
        self.flagged = set()
        self.status = "playing"

    def neighbours(self, cell: int) -> list[int]:
        row, column = divmod(cell, self.columns)
        return [
            neighbour_row * self.columns + neighbour_column
            for neighbour_row in range(max(0, row - 1), min(self.rows, row + 2))
            for neighbour_column in range(max(0, column - 1), min(self.columns, column + 2))
            if (neighbour_row, neighbour_column) != (row, column)
        ]

    def adjacent_mines(self, cell: int) -> int:
        return sum(neighbour in self.mines for neighbour in self.neighbours(cell))

    def reveal(self, cell: int) -> tuple[bool, str | None]:
        if self.status != "playing":
            return False, "This round is over. Start a new one to play again."
        if not isinstance(cell, int) or not 0 <= cell < self.total_cells:
            return False, "Choose a valid board cell."
        if cell in self.flagged:
            return False, "Unflag this cell before revealing it."
        if cell in self.revealed:
            return False, "That cell is already revealed."
        if cell in self.mines:
            self.revealed.update(self.mines)
            self.status = "lost"
            return True, None

        # Flood-fill empty spaces so one reveal feels responsive and natural.
        pending = [cell]
        while pending:
            current = pending.pop()
            if current in self.revealed or current in self.mines or current in self.flagged:
                continue
            self.revealed.add(current)
            if self.adjacent_mines(current) == 0:
                pending.extend(self.neighbours(current))
        if len(self.revealed) == self.total_cells - self.mine_count:
            self.status = "won"
            self.flagged = set(self.mines)
        return True, None

    def toggle_flag(self, cell: int) -> tuple[bool, str | None]:
        if self.status != "playing":
            return False, "This round is over. Start a new one to play again."
        if not isinstance(cell, int) or not 0 <= cell < self.total_cells:
            return False, "Choose a valid board cell."
        if cell in self.revealed:
            return False, "Revealed cells cannot be flagged."
        if cell in self.flagged:
            self.flagged.remove(cell)
        elif len(self.flagged) < self.mine_count:
            self.flagged.add(cell)
        else:
            return False, "All flags are already in use."
        return True, None

    def state(self, error: str | None = None) -> dict:
        cells = []
        for cell in range(self.total_cells):
            mine = cell in self.mines
            cells.append({
                "revealed": cell in self.revealed,
                "flagged": cell in self.flagged,
                "mine": mine if self.status != "playing" else False,
                "count": self.adjacent_mines(cell) if cell in self.revealed and not mine else 0,
            })
        data = {"rows": self.rows, "columns": self.columns, "mine_count": self.mine_count,
                "flags_left": self.mine_count - len(self.flagged), "status": self.status, "cells": cells}
        if error:
            data["error"] = error
        return data
