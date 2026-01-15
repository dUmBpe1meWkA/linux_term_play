// ===== crash diagnostics (shows errors on screen) =====
window.addEventListener("error", (e) => {
  const msg = e?.error?.stack || e?.message || String(e);
  try {
    const pre = document.createElement("pre");
    pre.style.whiteSpace = "pre-wrap";
    pre.style.fontSize = "12px";
    pre.style.padding = "12px";
    pre.style.color = "#ff9aa2";
    pre.textContent = "JS ERROR:\n" + msg;
    document.body.appendChild(pre);
  } catch {}
});

window.addEventListener("unhandledrejection", (e) => {
  const msg = e?.reason?.stack || e?.reason?.message || String(e?.reason);
  try {
    const pre = document.createElement("pre");
    pre.style.whiteSpace = "pre-wrap";
    pre.style.fontSize = "12px";
    pre.style.padding = "12px";
    pre.style.color = "#ffdf91";
    pre.textContent = "PROMISE REJECTION:\n" + msg;
    document.body.appendChild(pre);
  } catch {}
});

// ===== UI refs =====
//const lessonSelect = document.getElementById("lessonSelect");
const lessonBtn  = document.getElementById("lessonBtn");
const lessonText = document.getElementById("lessonText");
const lessonMenu = document.getElementById("lessonMenu");

const startOverlay = document.getElementById("startOverlay");
const btnContinue = document.getElementById("btnContinue");
const btnNew = document.getElementById("btnNew");
const taskTitle = document.getElementById("taskTitle");
const resetBtn = document.getElementById("resetBtn");
const taskPrompt = document.getElementById("taskPrompt");
const cwdChip = document.getElementById("cwdChip");
const taskChip = document.getElementById("taskChip");
const hintBtn = document.getElementById("hintBtn");
const hintBox = document.getElementById("hintBox");

const progressText = document.getElementById("progressText");
const progressFill = document.getElementById("progressFill");
let lessons = [];
let selectedLessonId = "01_paths";

// ===== xterm =====
const term = new Terminal({
  cursorBlink: true,
  cursorStyle: "block",
  fontFamily:
    "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace",
  fontSize: 14,
  theme: {
    background: "#0b0f19",
    foreground: "#e8eefc",
  },
});

term.open(document.getElementById("terminal"));
term.writeln("Linux Trainer — локальная обучающая игра.");
term.writeln("Введите команду и нажмите Enter.");
term.writeln("");

// ===== line editor state =====
let buffer = "";
let cursor = 0; // 0..buffer.length

// ===== history =====
const history = [];
let historyIndex = -1;
let savedLineBeforeHistory = "";
btnContinue.addEventListener("click", async () => {
  const lessonId = selectedLessonId || "01_paths";
  const payload = await window.pywebview.api.continue_game(lessonId);
  setTaskUI(payload);
  term.writeln("");
  printPrompt(payload.cwd);
  showOverlay(false);
});


btnNew.addEventListener("click", async () => {
  const lessonId = selectedLessonId || "01_paths";
  const payload = await window.pywebview.api.start_new(lessonId);

  term.clear();
  term.writeln("Linux Trainer — локальная обучающая игра.");
  term.writeln("Введите команду и нажмите Enter.");
  term.writeln("");

  setTaskUI(payload);
  term.writeln("");
  printPrompt(payload.cwd);
  showOverlay(false);
});


lessonBtn.addEventListener("click", () => {
  const isOpen = !lessonMenu.classList.contains("hidden");
  openLessonMenu(!isOpen);
});

// закрытие по клику вне
document.addEventListener("click", (e) => {
  if (!e.target.closest("#lessonDD")) openLessonMenu(false);
});

// закрытие по Esc
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") openLessonMenu(false);
});

function openLessonMenu(open) {
  if (open) lessonMenu.classList.remove("hidden");
  else lessonMenu.classList.add("hidden");
}

function renderLessons() {
  lessonMenu.innerHTML = "";

  for (const l of lessons) {
    const item = document.createElement("div");
    item.className = "lesson-dd__item" + (l.id === selectedLessonId ? " lesson-dd__item--active" : "");
    item.innerHTML = `
      <div>${l.title}</div>
    `;

    item.addEventListener("click", async () => {
  selectedLessonId = l.id;

  if (window.pywebview?.api?.has_save) {
    const s = await window.pywebview.api.has_save(selectedLessonId);
    btnContinue.disabled = !s.has_save;
  }

  lessonText.textContent = l.title;
  renderLessons();
  openLessonMenu(false);
});


    lessonMenu.appendChild(item);
  }
}

function showOverlay(show) {
  if (show) startOverlay.classList.remove("hidden");
  else startOverlay.classList.add("hidden");
}

async function boot() {
  if (!(window.pywebview && window.pywebview.api && typeof window.pywebview.api.get_task === "function")) {
    setTimeout(boot, 50);
    return;
  }

  try {
  const list = await window.pywebview.api.list_lessons();
  lessons = list.lessons || [];

  if (lessons.length === 0) {
    lessons = [{ id: "01_paths", title: "01 — Пути и навигация" }];
  }

  selectedLessonId = lessons[0].id;
  lessonText.textContent = lessons[0].title;
  renderLessons();
} catch (e) {
  console.log("list_lessons failed:", e);
}


  const s = await window.pywebview.api.has_save(selectedLessonId);
  btnContinue.disabled = !s.has_save;


  showOverlay(true);
}




// ===== helpers: cursor movement =====
function moveCursorLeft(n) {
  if (n > 0) term.write(`\x1b[${n}D`);
}
function moveCursorRight(n) {
  if (n > 0) term.write(`\x1b[${n}C`);
}
function clearToEnd() {
  term.write("\x1b[K");
}

// redraw tail from cursor to end
function redrawFromCursor() {
  const tail = buffer.slice(cursor);
  clearToEnd();
  term.write(tail);
  moveCursorLeft(tail.length);
}

function insertText(text) {
  if (!text) return;
  buffer = buffer.slice(0, cursor) + text + buffer.slice(cursor);
  cursor += text.length;
  term.write(text);
  redrawFromCursor();
}

function backspace() {
  if (cursor === 0) return;
  buffer = buffer.slice(0, cursor - 1) + buffer.slice(cursor);
  cursor -= 1;
  moveCursorLeft(1);
  redrawFromCursor();
}

function del() {
  if (cursor >= buffer.length) return;
  buffer = buffer.slice(0, cursor) + buffer.slice(cursor + 1);
  redrawFromCursor();
}

function cursorLeft() {
  if (cursor === 0) return;
  cursor -= 1;
  moveCursorLeft(1);
}

function cursorRight() {
  if (cursor >= buffer.length) return;
  cursor += 1;
  moveCursorRight(1);
}

function cursorHome() {
  const n = cursor;
  cursor = 0;
  moveCursorLeft(n);
}

function cursorEnd() {
  const n = buffer.length - cursor;
  cursor = buffer.length;
  moveCursorRight(n);
}

function setBuffer(text) {
  // стереть текущую строку ввода на экране: в начало и clear-to-end
  cursorHome();
  clearToEnd();
  buffer = text;
  cursor = buffer.length;
  term.write(buffer);
}

// ===== clipboard =====
async function pasteFromClipboard() {
  try {
    const text = await navigator.clipboard.readText();
    if (!text) return;
    insertText(text.replace(/\r/g, "").replace(/\n/g, ""));
  } catch {
    // clipboard can be blocked in some WebView contexts; ignore silently
  }
}

// ===== UI render =====
function setTaskUI(payload) {
  const t = payload.task;
  taskTitle.textContent = t.title;
  taskPrompt.textContent = t.prompt;

  cwdChip.textContent = `cwd: ${payload.cwd}`;
  taskChip.textContent = `task: ${t.id}`;

  const p = payload.progress;
  progressText.textContent = `Задание ${p.index} / ${p.total} • Верно: ${p.correct} • Попыток: ${p.attempts}`;
  const percent = Math.round(((p.index - 1) / p.total) * 100);
  progressFill.style.width = `${percent}%`;

  hintBox.classList.add("hidden");
  hintBox.textContent = "";
}

function appendTerminalLines(lines) {
  lines.forEach((line) => term.writeln(line));
}

function pushHistory(cmd) {
  const c = cmd.trim();
  if (!c) return;
  if (history.length > 0 && history[history.length - 1] === c) return;
  history.push(c);
}
function printPrompt(cwd) {
  term.write(`student@trainer:${cwd}$ `); // важно: write, НЕ writeln
}


// ===== start / init =====
async function loadInitialTask() {
  const payload = await window.pywebview.api.get_task();
  setTaskUI(payload);

  term.writeln("");
  printPrompt(payload.cwd);
}

// ===== input handling =====
term.onKey(async (e) => {
  const ev = e.domEvent;
  const key = ev.key;

  // paste
  if ((ev.ctrlKey && key.toLowerCase() === "v") || (ev.shiftKey && key === "Insert")) {
    ev.preventDefault();
    await pasteFromClipboard();
    return;
  }

  // copy (leave default)
  if (ev.ctrlKey && key.toLowerCase() === "c") {
    return;
  }

  // arrows editing
  if (key === "ArrowLeft") {
    ev.preventDefault();
    cursorLeft();
    return;
  }
  if (key === "ArrowRight") {
    ev.preventDefault();
    cursorRight();
    return;
  }
  if (key === "Home") {
    ev.preventDefault();
    cursorHome();
    return;
  }
  if (key === "End") {
    ev.preventDefault();
    cursorEnd();
    return;
  }


  if (key === "ArrowUp") {
    ev.preventDefault();
    if (history.length === 0) return;

    if (historyIndex === -1) {
      savedLineBeforeHistory = buffer;
      historyIndex = history.length - 1;
    } else {
      historyIndex = Math.max(0, historyIndex - 1);
    }
    setBuffer(history[historyIndex]);
    return;
  }

  if (key === "ArrowDown") {
    ev.preventDefault();
    if (history.length === 0) return;
    if (historyIndex === -1) return;

    historyIndex = Math.min(history.length, historyIndex + 1);
    if (historyIndex === history.length) {
      historyIndex = -1;
      setBuffer(savedLineBeforeHistory);
    } else {
      setBuffer(history[historyIndex]);
    }
    return;
  }

  // backspace/delete
  if (key === "Backspace") {
    ev.preventDefault();
    backspace();
    return;
  }
  if (key === "Delete") {
    ev.preventDefault();
    del();
    return;
  }

  // enter
  if (key === "Enter") {
  ev.preventDefault();

  const cmd = buffer.trimEnd();
  pushHistory(cmd);
  historyIndex = -1;
  savedLineBeforeHistory = "";

  // как в терминале: Enter завершает строку ввода
  term.writeln("");

  // reset editor
  buffer = "";
  cursor = 0;

  const res = await window.pywebview.api.submit_command(cmd);

  // Python теперь возвращает ТОЛЬКО вывод (без prompt+command)
  appendTerminalLines(res.terminal_lines);
  setTaskUI({ task: res.task, cwd: res.cwd, progress: res.progress });

  // новый prompt
  term.writeln("");
  printPrompt(res.cwd);
  return;
}

  // printable character
  if (key.length === 1 && !ev.ctrlKey && !ev.metaKey && !ev.altKey) {
    ev.preventDefault();
    insertText(key);
  }
});

// ===== hint button =====
hintBtn.addEventListener("click", async () => {
  const res = await window.pywebview.api.get_hint();
  hintBox.textContent = res.hint;
  hintBox.classList.remove("hidden");
});
resetBtn.addEventListener("click", async () => {
  const lessonId = selectedLessonId || "01_paths";
  const payload = await window.pywebview.api.reset_progress(lessonId);
  setTaskUI(payload);
  term.writeln("\r\n--- прогресс сброшен ---\r\n");
  printPrompt(payload.cwd);
});

boot();