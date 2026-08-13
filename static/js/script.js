const settings = { mode: "computer", player_mark: "X", difficulty: "medium" };
const defaultSettings = { mode: "computer", player_mark: "X", difficulty: "medium" };
let state = null;
let submittingMove = false;

const board = document.querySelector("#board");
const statusMessage = document.querySelector("#status-message");
const toast = document.querySelector("#toast");

async function request(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Something went wrong.");
  return data;
}

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("show");
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => toast.classList.remove("show"), 2600);
}

function statusText(game) {
  if (game.status === "won") return `${game.winner} wins this round!`;
  if (game.status === "draw") return "It’s a draw — great battle.";
  if (game.mode === "computer") {
    return game.turn === game.player_mark ? "Your turn — make it count." : "Computer is thinking…";
  }
  return `Player ${game.turn}’s turn`;
}

function render(game) {
  state = game;
  board.innerHTML = "";
  const playable = game.status === "playing" && (game.mode === "player" || game.turn === game.player_mark) && !submittingMove;
  game.board.forEach((mark, cell) => {
    const button = document.createElement("button");
    button.className = `cell ${mark ? `mark-${mark.toLowerCase()}` : ""}`;
    button.type = "button";
    button.setAttribute("role", "gridcell");
    button.setAttribute("aria-label", mark ? `Cell ${cell + 1}: ${mark}` : `Empty cell ${cell + 1}`);
    button.disabled = Boolean(mark) || !playable;
    if (game.winning_cells.includes(cell)) button.classList.add("winner");
    if (mark) button.innerHTML = `<span>${mark}</span>`;
    button.addEventListener("click", () => playMove(cell));
    board.append(button);
  });
  statusMessage.textContent = statusText(game);
  document.querySelector("#turn-dot").className = `turn-dot ${game.status === "won" ? "complete" : game.turn === "X" ? "x" : "o"}`;
  document.querySelector("#score-x").textContent = game.scores.X;
  document.querySelector("#score-o").textContent = game.scores.O;
  document.querySelector("#score-draws").textContent = game.scores.draws;
}

async function playMove(cell) {
  if (submittingMove || !state) return;
  submittingMove = true;
  render(state);
  try {
    render(await request("/api/game/move", { method: "POST", body: JSON.stringify({ cell }) }));
  } catch (error) {
    showToast(error.message);
  } finally {
    submittingMove = false;
    if (state) render(state);
  }
}

async function startNewGame() {
  try {
    render(await request("/api/game/new", { method: "POST", body: JSON.stringify(settings) }));
  } catch (error) { showToast(error.message); }
}

function syncSettingsControls() {
  document.querySelectorAll("[data-mode]").forEach((button) => {
    button.classList.toggle("active", button.dataset.mode === settings.mode);
  });
  document.querySelectorAll("[data-difficulty]").forEach((button) => {
    button.classList.toggle("active", button.dataset.difficulty === settings.difficulty);
  });
  document.querySelectorAll("[data-mark]").forEach((button) => {
    button.classList.toggle("active", button.dataset.mark === settings.player_mark);
  });
  document.querySelector("#difficulty-group").classList.toggle("disabled", settings.mode === "player");
}

async function resetSetup() {
  Object.assign(settings, defaultSettings);
  syncSettingsControls();
  await startNewGame();
}

document.querySelectorAll("[data-mode]").forEach((button) => button.addEventListener("click", () => {
  settings.mode = button.dataset.mode;
  document.querySelectorAll("[data-mode]").forEach((item) => item.classList.toggle("active", item === button));
  document.querySelector("#difficulty-group").classList.toggle("disabled", settings.mode === "player");
}));
document.querySelectorAll("[data-difficulty]").forEach((button) => button.addEventListener("click", () => {
  settings.difficulty = button.dataset.difficulty;
  document.querySelectorAll("[data-difficulty]").forEach((item) => item.classList.toggle("active", item === button));
}));
document.querySelectorAll("[data-mark]").forEach((button) => button.addEventListener("click", () => {
  settings.player_mark = button.dataset.mark;
  document.querySelectorAll("[data-mark]").forEach((item) => item.classList.toggle("active", item === button));
}));
document.querySelector("#new-game").addEventListener("click", startNewGame);
document.querySelector("#new-game-mobile").addEventListener("click", () => {
  resetSetup().catch((error) => showToast(error.message));
});
document.querySelector("#restart-game").addEventListener("click", async () => {
  try { render(await request("/api/game/restart", { method: "POST" })); } catch (error) { showToast(error.message); }
});
document.querySelector("#reset-scores").addEventListener("click", async () => {
  try { render(await request("/api/scores/reset", { method: "POST" })); showToast("Scoreboard reset."); } catch (error) { showToast(error.message); }
});
document.querySelector("#theme-toggle").addEventListener("click", () => {
  document.body.classList.toggle("light-theme");
  const light = document.body.classList.contains("light-theme");
  document.querySelector("#theme-toggle span").textContent = light ? "☾" : "☼";
  localStorage.setItem("ttt-theme", light ? "light" : "dark");
});
if (localStorage.getItem("ttt-theme") === "light") document.querySelector("#theme-toggle").click();

request("/api/game").then(render).catch((error) => showToast(error.message));
