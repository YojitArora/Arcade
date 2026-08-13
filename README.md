# TicTacToe

A small shared arcade built with Flask and vanilla HTML/CSS/JavaScript. It includes TicTacToe and Minesweeper under one consistent interface.

## Features

- Player vs Player and Player vs Computer modes
- Easy (random), Medium (win/block strategy), and Hard (optimal Minimax) computer opponents
- Choose whether the human player is X or O
- Server-validated moves, wins, draws, and score tracking
- Session scoreboard, winning-cell animation, responsive layout, and light/dark themes
- A responsive game switcher and a server-validated 9×9 Minesweeper game

## Run locally

1. Create and activate a virtual environment (recommended):

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install Flask:

   ```bash
   pip install -r requirements.txt
   ```

3. Start the app:

   ```bash
   python app.py
   ```

4. Open http://127.0.0.1:5050 in your browser.

## Project layout

`app.py` provides the Flask pages and JSON APIs. `game.py` owns TicTacToe's rules, validation, score keeping, and Minimax implementation; `minesweeper.py` owns the Minesweeper board rules. Each frontend renders server state and sends requested moves.

Scores are intentionally held in memory for the current running server session. Restarting the server resets them.

## API

- `GET /api/game` — current state
- `POST /api/game/new` — begin a game with `mode`, `player_mark`, and `difficulty`
- `POST /api/game/move` — send `{ "cell": 0 }` through `{ "cell": 8 }`
- `POST /api/game/restart` — clear the board and preserve scores
- `POST /api/scores/reset` — reset session scores
- `GET /api/minesweeper` — current Minesweeper state
- `POST /api/minesweeper/new` — start a new Minesweeper round
- `POST /api/minesweeper/reveal` — reveal a cell with `{ "cell": 0 }`
- `POST /api/minesweeper/flag` — toggle a cell flag with `{ "cell": 0 }`
