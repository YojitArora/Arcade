"""Flask entry point for the shared Arcade web application."""

import json
import re
import threading
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from game import O, X, TicTacToeGame
from minesweeper import MinesweeperGame

app = Flask(__name__)
game = TicTacToeGame()
minesweeper = MinesweeperGame()
SCORES_FILE = Path(__file__).with_name("minesweeper_scores.json")
scores_lock = threading.Lock()
BOARD_PATTERN = re.compile(r"^([1-9][0-9]?)x([1-9][0-9]?)$")


def payload() -> dict:
    return request.get_json(silent=True) or {}


def read_minesweeper_scores() -> list[dict]:
    """Read saved score records, treating a missing or invalid file as empty."""
    try:
        with SCORES_FILE.open(encoding="utf-8") as score_file:
            scores = json.load(score_file)
        return scores if isinstance(scores, list) else []
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return []


def write_minesweeper_scores(scores: list[dict]) -> None:
    temporary_file = SCORES_FILE.with_suffix(".tmp")
    with temporary_file.open("w", encoding="utf-8") as score_file:
        json.dump(scores, score_file, ensure_ascii=False, indent=2)
    temporary_file.replace(SCORES_FILE)


def score_record(record: dict) -> dict:
    """Return only the public score fields, never the internal numeric id."""
    return {key: record[key] for key in ("name", "time", "moves", "board", "date", "won")}


def valid_score_record(record: object) -> bool:
    return (
        isinstance(record, dict)
        and isinstance(record.get("name"), str)
        and isinstance(record.get("time"), int)
        and not isinstance(record.get("time"), bool)
        and isinstance(record.get("moves"), int)
        and not isinstance(record.get("moves"), bool)
        and isinstance(record.get("board"), str)
        and isinstance(record.get("date"), str)
        and isinstance(record.get("won"), bool)
    )


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/minesweeper")
def minesweeper_page():
    return render_template("minesweeper.html")


@app.get("/api/game")
def get_game():
    """Return the current server-authoritative game state."""
    return jsonify(game.state())


@app.post("/api/game/new")
def new_game():
    """Configure and start a fresh round; scoreboard remains intact."""
    data = payload()
    mode = data.get("mode", "computer")
    player_mark = data.get("player_mark", X)
    difficulty = data.get("difficulty", "medium")
    if mode not in {"player", "computer"} or player_mark not in {X, O} or difficulty not in {"easy", "medium", "hard"}:
        return jsonify(game.state("Invalid game settings.")), 400
    game.new_game(mode, player_mark, difficulty)
    return jsonify(game.state())


@app.post("/api/game/restart")
def restart_game():
    game.restart()
    return jsonify(game.state())


@app.post("/api/game/move")
def make_move():
    """Apply a validated player move. The server triggers the computer move too."""
    data = payload()
    cell = data.get("cell")
    success, error = game.move(cell)
    return jsonify(game.state(error)), 200 if success else 400


@app.post("/api/scores/reset")
def reset_scores():
    game.reset_scores()
    return jsonify(game.state())


@app.get("/api/minesweeper")
def get_minesweeper():
    return jsonify(minesweeper.state())


@app.post("/api/minesweeper/new")
def new_minesweeper():
    minesweeper.new_game()
    return jsonify(minesweeper.state())


@app.post("/api/minesweeper/reveal")
def reveal_minesweeper():
    success, error = minesweeper.reveal(payload().get("cell"))
    return jsonify(minesweeper.state(error)), 200 if success else 400


@app.post("/api/minesweeper/flag")
def flag_minesweeper():
    success, error = minesweeper.toggle_flag(payload().get("cell"))
    return jsonify(minesweeper.state(error)), 200 if success else 400


@app.get("/scores")
def get_scores():
    board = request.args.get("board", "")
    if not BOARD_PATTERN.fullmatch(board):
        return jsonify(error="board must use the format rowsxcolumns, for example 9x9."), 400
    try:
        limit = int(request.args.get("limit", 10))
    except ValueError:
        return jsonify(error="limit must be a whole number."), 400
    if not 1 <= limit <= 100:
        return jsonify(error="limit must be between 1 and 100."), 400

    with scores_lock:
        scores = [score for score in read_minesweeper_scores() if valid_score_record(score) and score["board"] == board]
    scores.sort(key=lambda score: (not score.get("won", False), score.get("time", 0), score.get("moves", 0), score.get("id", 0)))
    return jsonify(scores=[score_record(score) for score in scores[:limit]])


@app.post("/scores")
def save_score():
    data = payload()
    name = data.get("name")
    board = data.get("board")
    elapsed_time = data.get("time")
    moves = data.get("moves")
    won = data.get("won")

    if not isinstance(name, str):
        return jsonify(error="name is required."), 400
    name = " ".join(name.split())
    if not 1 <= len(name) <= 24:
        return jsonify(error="name must be between 1 and 24 characters."), 400
    if not isinstance(board, str) or not BOARD_PATTERN.fullmatch(board):
        return jsonify(error="board must use the format rowsxcolumns, for example 9x9."), 400
    if isinstance(elapsed_time, bool) or not isinstance(elapsed_time, int) or not 0 <= elapsed_time <= 86_400:
        return jsonify(error="time must be a number of seconds between 0 and 86400."), 400
    if isinstance(moves, bool) or not isinstance(moves, int) or not 0 <= moves <= 100_000:
        return jsonify(error="moves must be a whole number between 0 and 100000."), 400
    if not isinstance(won, bool):
        return jsonify(error="won must be true or false."), 400

    with scores_lock:
        scores = read_minesweeper_scores()
        next_id = max((score.get("id", 0) for score in scores if isinstance(score, dict) and isinstance(score.get("id", 0), int)), default=0) + 1
        record = {
            "id": next_id,
            "name": name,
            "time": elapsed_time,
            "moves": moves,
            "board": board,
            "won": won,
            "date": datetime.now(timezone.utc).date().isoformat(),
        }
        scores.append(record)
        write_minesweeper_scores(scores)
    return jsonify(ok=True, id=next_id), 201


if __name__ == "__main__":
    # Port 5050 avoids the commonly occupied default Flask port (5000).
    app.run(debug=True, port=5050)
