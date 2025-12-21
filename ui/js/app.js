// ----- UI refs -----
const taskTitle = document.getElementById("taskTitle");
const taskPrompt = document.getElementById("taskPrompt");
const cwdChip   = document.getElementById("cwdChip");
const taskChip  = document.getElementById("taskChip");
const hintBtn   = document.getElementById("hintBtn");
const hintBox   = document.getElementById("hintBox");

const progressText = document.getElementById("progressText");
const progressFill = document.getElementById("progressFill");

// ----- xterm -----
const term = new Terminal({
  cursorBlink: true,
  fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace",
  fontSize: 14,
  theme: {
    background: "#0b0f19",
    foreground: "#e8eefc"
  }
});

term.open(document.getElementById("terminal"));
term.writeln("Linux Trainer — локальная обучающая игра.");
term.writeln("Введите команду и нажмите Enter.");
term.writeln("");

let currentLine = "";
// ----- command history -----
const history = [];
let historyIndex = -1; // -1 = "не в истории"
let savedLineBeforeHistory = "";

function clearCurrentInput() {
  // стираем текущую набранную строку с экрана
  while (currentLine.length > 0) {
    term.write("\b \b");
    currentLine = currentLine.slice(0, -1);
  }
}

function setCurrentInput(text) {
  clearCurrentInput();
  currentLine = text;
  term.write(text);
}

function pushHistory(cmd) {
  const c = cmd.trim();
  if (!c) return;
  // не дублируем одинаковые команды подряд
  if (history.length > 0 && history[history.length - 1] === c) return;
  history.push(c);
}

// ----- clipboard helpers -----
async function pasteFromClipboard() {
  try {
    const text = await navigator.clipboard.readText();
    if (text) {
      // вставляем как будто пользователь напечатал
      for (const ch of text.replace(/\r/g, "")) {
        if (ch === "\n") continue; // не позволяем вставкой отправить Enter
        currentLine += ch;
        term.write(ch);
      }
    }
  } catch (e) {
    term.writeln("\r\n❌ Вставка недоступна: браузер/окно запретили доступ к буферу обмена.");
    printPrompt(document.getElementById("cwdChip").textContent.replace("cwd: ", ""));
  }
}


// Печать подсказочного промпта (чисто визуально)
function printPrompt(cwd) {
  term.write(`student@trainer:${cwd}$ `);
}

// ----- helpers -----
function setTaskUI(payload) {
  const t = payload.task;
  taskTitle.textContent = t.title;
  taskPrompt.textContent = t.prompt;
  cwdChip.textContent = `cwd: ${payload.cwd}`;
  taskChip.textContent = `task: ${t.id}`;

  // прогресс
  const p = payload.progress;
  progressText.textContent = `Задание ${p.index} / ${p.total} • Верно: ${p.correct} • Попыток: ${p.attempts}`;
  const percent = Math.round((p.index - 1) / p.total * 100);
  progressFill.style.width = `${percent}%`;

  // скрываем подсказку при переходе
  hintBox.classList.add("hidden");
  hintBox.textContent = "";

  // печатаем промпт для нового ввода
  term.writeln("");
  printPrompt(res.cwd);
}

function appendTerminalLines(lines) {
  // Мы уже печатаем prompt отдельно, но Python тоже возвращает строку prompt+command.
  // Чтобы не было дубля — мы в MVP будем печатать то, что прислал Python, и НЕ печатать локально.
  // Поэтому printPrompt() выше используется только после загрузки/перехода задачи.
  lines.forEach(line => term.writeln(line));
}

async function loadInitialTask() {
  const payload = await window.pywebview.api.get_task();
  term.writeln("");
  setTaskUI(payload);
}

// ----- input handling -----
term.onKey(async (e) => {
  const ev = e.domEvent;
  const key = ev.key;

  // Ctrl+V / Shift+Insert — вставка
  if ((ev.ctrlKey && key.toLowerCase() === "v") || (ev.shiftKey && key === "Insert")) {
    ev.preventDefault();
    await pasteFromClipboard();
    return;
  }

  // Ctrl+C — если есть выделение, пусть копирует стандартно
  // (мы не блокируем, чтобы работало копирование выделенного текста)
  if (ev.ctrlKey && key.toLowerCase() === "c") {
    return;
  }

  // История команд стрелками
  if (key === "ArrowUp") {
    ev.preventDefault();
    if (history.length === 0) return;

    if (historyIndex === -1) {
      savedLineBeforeHistory = currentLine;
      historyIndex = history.length - 1;
    } else {
      historyIndex = Math.max(0, historyIndex - 1);
    }

    setCurrentInput(history[historyIndex]);
    return;
  }

  if (key === "ArrowDown") {
    ev.preventDefault();
    if (history.length === 0) return;
    if (historyIndex === -1) return;

    historyIndex = Math.min(history.length, historyIndex + 1);
    if (historyIndex === history.length) {
      historyIndex = -1;
      setCurrentInput(savedLineBeforeHistory);
    } else {
      setCurrentInput(history[historyIndex]);
    }
    return;
  }

  // Enter — отправка команды
  if (key === "Enter") {
    ev.preventDefault();

    const cmd = currentLine.trimEnd();
    pushHistory(cmd);
    historyIndex = -1;
    savedLineBeforeHistory = "";

    currentLine = "";

    const res = await window.pywebview.api.submit_command(cmd);

    appendTerminalLines(res.terminal_lines);
    // показать код ошибки/успеха (необязательно)
    if (res.feedback && res.feedback.code && res.feedback.code !== "OK") {
    term.writeln(`[${res.feedback.code}]`);
    }


    term.writeln("");
    printPrompt(res.cwd);

    setTaskUI({ task: res.task, cwd: res.cwd, progress: res.progress });
    return;
  }

  // Backspace
  if (key === "Backspace") {
    ev.preventDefault();
    if (currentLine.length > 0) {
      currentLine = currentLine.slice(0, -1);
      term.write("\b \b");
    }
    return;
  }

  // Печатаемые символы
  // (игнорируем всякие функциональные клавиши)
  if (key.length === 1 && !ev.ctrlKey && !ev.metaKey && !ev.altKey) {
    currentLine += key;
    term.write(key);
  }
});


// ----- hint button -----
hintBtn.addEventListener("click", async () => {
  const res = await window.pywebview.api.get_hint();
  hintBox.textContent = res.hint;
  hintBox.classList.remove("hidden");
});

// ----- start -----
loadInitialTask();
