"""Server-side Tic-Tac-Toe rules and computer opponents."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Optional

X, O, EMPTY = "X", "O", ""
WINNING_LINES = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6),
)


def other(mark: str) -> str:
    return O if mark == X else X


def winner(board: list[str]) -> tuple[Optional[str], list[int]]:
    """Return the winning mark and its cells, if the board has a winner."""
    for line in WINNING_LINES:
        a, b, c = line
        if board[a] and board[a] == board[b] == board[c]:
            return board[a], list(line)
    return None, []


def available_moves(board: list[str]) -> list[int]:
    return [index for index, cell in enumerate(board) if not cell]


def _minimax(board: list[str], turn: str, ai_mark: str, depth: int = 0) -> int:
    """Score positions recursively so the AI chooses an unbeatable move.

    Positive scores favour the computer, negative scores favour its opponent.
    Depth rewards faster wins and delays unavoidable losses.
    """
    victor, _ = winner(board)
    if victor == ai_mark:
        return 10 - depth
    if victor == other(ai_mark):
        return depth - 10
    moves = available_moves(board)
    if not moves:
        return 0

    scores = []
    for move in moves:
        board[move] = turn
        scores.append(_minimax(board, other(turn), ai_mark, depth + 1))
        board[move] = EMPTY
    return max(scores) if turn == ai_mark else min(scores)


def hard_move(board: list[str], ai_mark: str) -> int:
    """Choose the best move using Minimax, breaking equal ties naturally."""
    best_score = -float("inf")
    best_move = available_moves(board)[0]
    for move in available_moves(board):
        board[move] = ai_mark
        score = _minimax(board, other(ai_mark), ai_mark)
        board[move] = EMPTY
        if score > best_score:
            best_score, best_move = score, move
    return best_move


def medium_move(board: list[str], ai_mark: str) -> int:
    """A lightweight opponent: win, block, take centre/corners, then random."""
    opponent = other(ai_mark)
    for mark in (ai_mark, opponent):
        for move in available_moves(board):
            board[move] = mark
            is_win = winner(board)[0] == mark
            board[move] = EMPTY
            if is_win:
                return move
    for preferred in (4, 0, 2, 6, 8):
        if not board[preferred]:
            return preferred
    return random.choice(available_moves(board))


@dataclass
class TicTacToeGame:
    """One in-memory game session managed by the Flask application."""

    board: list[str] = field(default_factory=lambda: [EMPTY] * 9)
    mode: str = "computer"
    player_mark: str = X
    difficulty: str = "medium"
    turn: str = X
    status: str = "playing"
    winner_mark: Optional[str] = None
    winning_cells: list[int] = field(default_factory=list)
    scores: dict[str, int] = field(default_factory=lambda: {X: 0, O: 0, "draws": 0})

    @property
    def computer_mark(self) -> str:
        return other(self.player_mark)

    def new_game(self, mode: str = "computer", player_mark: str = X, difficulty: str = "medium") -> None:
        self.board = [EMPTY] * 9
        self.mode = mode
        self.player_mark = player_mark
        self.difficulty = difficulty
        self.turn = X
        self.status = "playing"
        self.winner_mark = None
        self.winning_cells = []
        # X always opens. If the human chose O, let the computer take X now.
        if self.mode == "computer" and self.player_mark == O:
            self._computer_move()

    def restart(self) -> None:
        """Start another round with the selected settings while retaining scores."""
        self.new_game(self.mode, self.player_mark, self.difficulty)

    def reset_scores(self) -> None:
        self.scores = {X: 0, O: 0, "draws": 0}

    def state(self, error: Optional[str] = None) -> dict:
        data = {
            "board": self.board,
            "mode": self.mode,
            "player_mark": self.player_mark,
            "computer_mark": self.computer_mark if self.mode == "computer" else None,
            "difficulty": self.difficulty,
            "turn": self.turn,
            "status": self.status,
            "winner": self.winner_mark,
            "winning_cells": self.winning_cells,
            "scores": self.scores,
        }
        if error:
            data["error"] = error
        return data

    def _complete_if_needed(self) -> None:
        victor, cells = winner(self.board)
        if victor:
            self.status, self.winner_mark, self.winning_cells = "won", victor, cells
            self.scores[victor] += 1
        elif not available_moves(self.board):
            self.status = "draw"
            self.scores["draws"] += 1

    def _computer_move(self) -> None:
        """Choose and apply one legal move for the computer."""
        moves = available_moves(self.board)
        if self.difficulty == "easy":
            computer_cell = random.choice(moves)
        elif self.difficulty == "hard":
            computer_cell = hard_move(self.board, self.computer_mark)
        else:
            computer_cell = medium_move(self.board, self.computer_mark)
        self.board[computer_cell] = self.computer_mark
        self._complete_if_needed()
        if self.status == "playing":
            self.turn = other(self.turn)

    def move(self, cell: int) -> tuple[bool, Optional[str]]:
        """Validate and apply a move, including a computer reply when required."""
        if self.status != "playing":
            return False, "This round is already over. Start a new round to play again."
        if not isinstance(cell, int) or cell < 0 or cell > 8:
            return False, "Choose a valid board cell."
        if self.board[cell]:
            return False, "That cell is already occupied."
        if self.mode == "computer" and self.turn != self.player_mark:
            return False, "Please wait for the computer's move."

        self.board[cell] = self.turn
        self._complete_if_needed()
        if self.status == "playing":
            self.turn = other(self.turn)

        if self.mode == "computer" and self.status == "playing" and self.turn == self.computer_mark:
            self._computer_move()
        return True, None
