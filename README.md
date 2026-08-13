# TicTacToe

A small shared arcade built with Flask and vanilla HTML/CSS/JavaScript. It includes TicTacToe and Minesweeper under one consistent interface.

## Features

### TicTacToe
- Player vs Player and Player vs Computer modes
- Easy (random), Medium (win/block strategy), and Hard (optimal Minimax) computer opponents
- Choose whether the human player is X or O
- Server-validated moves, wins, draws, and score tracking
- Session scoreboard, winning-cell animation, responsive layout, and light/dark themes

### Minesweeper
- Classic 9×9 grid with configurable difficulty
- Reveal cells and flag suspected mines
- Server-validated board logic and win/loss detection
- Score tracking with game results history
- Recursive cell clearing (opens blank areas automatically)
- Mine counter and timer

### General
- Responsive game switcher
- Light/dark theme support
- Session-based scoreboard

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

`app.py` provides the Flask pages and JSON APIs for both games. 

**TicTacToe**: `game.py` owns the game's rules, validation, score keeping, and Minimax implementation for AI opponents.

**Minesweeper**: `minesweeper.py` handles the board generation, mine placement, cell revealing logic, flagging, and win/loss detection.

Each frontend renders server state and sends requested moves via API. Scores are intentionally held in memory for the current running server session. Restarting the server resets them.

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

## Minesweeper Gameplay

- **Objective**: Reveal all non-mine cells without hitting a mine
- **Reveal**: Click a cell to uncover it. If it's safe, it shows the number of adjacent mines (or blank if zero)
- **Flag**: Right-click or use the flag button to mark suspected mines
- **Cascade**: Revealing a cell with no adjacent mines automatically reveals all adjacent safe cells
- **Win**: Reveal all safe cells (mines stay flagged)
- **Lose**: Reveal a cell containing a mine

## Technologies

- **Backend**: Python with Flask
- **Frontend**: Vanilla HTML, CSS, and JavaScript
- **Storage**: JSON file for persistent score tracking (optional)
- **Board Size**: 9×9 grid with mines and numbers
