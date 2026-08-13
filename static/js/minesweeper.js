let minesState = null;
let flagMode = false;
let runStartedAt = Date.now();
let runEndedAt = null;
let runMoves = 0;
let runComplete = false;
let displayedBoard = null;
const minesBoard = document.querySelector("#mines-board");
const message = document.querySelector("#mines-message");
const toast = document.querySelector("#toast");
const runTime = document.querySelector("#run-time");
const runMovesElement = document.querySelector("#run-moves");
const runFlags = document.querySelector("#run-flags");
const runStatus = document.querySelector("#run-status");
const scoreBoardSize = document.querySelector("#score-board-size");
const saveScoreForm = document.querySelector("#save-score-form");
const playerName = document.querySelector("#player-name");
const highScores = document.querySelector("#high-scores");

async function request(url, options = {}) {
  const response = await fetch(url, { headers: { "Content-Type": "application/json" }, ...options });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Something went wrong.");
  return data;
}
function showToast(text) { toast.textContent = text; toast.classList.add("show"); clearTimeout(showToast.timer); showToast.timer = setTimeout(() => toast.classList.remove("show"), 2400); }
function statusText(status) { return status === "won" ? "Field cleared. You win." : status === "lost" ? "Mine triggered. Try again." : "Clear the field."; }
function boardSize(state) { return `${state.rows}x${state.columns}`; }
function elapsedSeconds() { return Math.floor(((runEndedAt || Date.now()) - runStartedAt) / 1000); }
function formatTime(seconds) { return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`; }
function updateRunStats() {
  if (!minesState) return;
  runTime.textContent = formatTime(elapsedSeconds());
  runMovesElement.textContent = runMoves;
  runFlags.textContent = minesState.mine_count - minesState.flags_left;
  runStatus.textContent = minesState.status[0].toUpperCase() + minesState.status.slice(1);
}
function renderScores(scores) {
  highScores.innerHTML = "";
  if (!scores.length) {
    highScores.innerHTML = '<li class="empty-score">No saved runs yet.</li>';
    return;
  }
  scores.forEach((score, index) => {
    const item = document.createElement("li");
    item.className = `high-score ${score.won ? "won-score" : "lost-score"}`;
    const rank = document.createElement("span");
    rank.textContent = `${index + 1}`;
    const name = document.createElement("strong");
    name.textContent = score.name;
    const details = document.createElement("span");
    details.textContent = `${formatTime(score.time)} · ${score.moves} moves · ${score.date}`;
    item.append(rank, name, details);
    highScores.append(item);
  });
}
async function loadScores(board) {
  try {
    const data = await request(`/scores?board=${encodeURIComponent(board)}&limit=10`);
    renderScores(data.scores);
  } catch (error) {
    highScores.innerHTML = '<li class="empty-score">Scores are unavailable.</li>';
    showToast(error.message);
  }
}
function render(state) {
  minesState = state;
  minesBoard.innerHTML = "";
  minesBoard.style.setProperty("--columns", state.columns);
  minesBoard.style.setProperty("--rows", state.rows);
  state.cells.forEach((cell, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `mine-cell ${cell.revealed ? "revealed" : ""} ${cell.mine ? "mine" : ""}`;
    button.disabled = cell.revealed || state.status !== "playing";
    button.setAttribute("role", "gridcell");
    button.setAttribute("aria-label", cell.revealed ? (cell.mine ? "Mine" : `${cell.count} nearby mines`) : "Covered cell");
    if (cell.flagged) button.textContent = "⚑";
    else if (cell.mine) button.textContent = "×";
    else if (cell.revealed && cell.count) button.textContent = cell.count;
    button.addEventListener("click", () => move(index));
    button.addEventListener("contextmenu", (event) => { event.preventDefault(); flag(index); });
    minesBoard.append(button);
  });
  message.textContent = statusText(state.status);
  document.querySelector("#flags-left").textContent = state.flags_left;
  const board = boardSize(state);
  scoreBoardSize.textContent = board;
  if (displayedBoard !== board) {
    displayedBoard = board;
    loadScores(board);
  }
  if (state.status !== "playing" && !runComplete) {
    runComplete = true;
    runEndedAt = Date.now();
    saveScoreForm.hidden = false;
    playerName.focus();
  }
  updateRunStats();
}
async function move(cell) { try { const state = await request(`/api/minesweeper/${flagMode ? "flag" : "reveal"}`, { method: "POST", body: JSON.stringify({ cell }) }); runMoves += 1; render(state); } catch (error) { showToast(error.message); } }
async function flag(cell) { try { const state = await request("/api/minesweeper/flag", { method: "POST", body: JSON.stringify({ cell }) }); runMoves += 1; render(state); } catch (error) { showToast(error.message); } }
document.querySelector("#mines-new-game").addEventListener("click", async () => { try { flagMode = false; runStartedAt = Date.now(); runEndedAt = null; runMoves = 0; runComplete = false; saveScoreForm.hidden = true; playerName.value = ""; updateFlagMode(); render(await request("/api/minesweeper/new", { method: "POST" })); } catch (error) { showToast(error.message); } });
function updateFlagMode() { const button = document.querySelector("#flag-mode"); button.textContent = `Flag mode: ${flagMode ? "on" : "off"}`; button.setAttribute("aria-pressed", String(flagMode)); }
document.querySelector("#flag-mode").addEventListener("click", () => { flagMode = !flagMode; updateFlagMode(); });
saveScoreForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!minesState) return;
  const button = saveScoreForm.querySelector("button");
  button.disabled = true;
  try {
    await request("/scores", { method: "POST", body: JSON.stringify({ name: playerName.value, time: elapsedSeconds(), moves: runMoves, board: boardSize(minesState), won: minesState.status === "won" }) });
    saveScoreForm.hidden = true;
    await loadScores(boardSize(minesState));
    showToast("Score saved.");
  } catch (error) {
    showToast(error.message);
  } finally {
    button.disabled = false;
  }
});
document.querySelector("#theme-toggle").addEventListener("click", () => { document.body.classList.toggle("light-theme"); const light = document.body.classList.contains("light-theme"); document.querySelector("#theme-toggle span").textContent = light ? "☾" : "☼"; localStorage.setItem("ttt-theme", light ? "light" : "dark"); });
if (localStorage.getItem("ttt-theme") === "light") document.querySelector("#theme-toggle").click();
request("/api/minesweeper").then(render).catch((error) => showToast(error.message));
setInterval(updateRunStats, 1000);
