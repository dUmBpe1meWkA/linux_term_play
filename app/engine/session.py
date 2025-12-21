from __future__ import annotations
from app.engine.vfs import VFS
import posixpath

from dataclasses import dataclass, asdict
from typing import Any

from app.engine.checker import check_command
from app.engine.lesson_loader import load_lesson_json


@dataclass(frozen=True)
class Task:
    id: str
    title: str
    prompt: str
    rule: dict[str, Any]
    hint: str
    success_explain: str


class Session:
    """
    Session = состояние прохождения:
    - cwd (виртуальная директория)
    - индекс задания
    - статистика
    - данные текущего урока (из JSON)
    """

    def __init__(self) -> None:
        self.last_cmd = ""
        self.home = "/home/student"
        self.vfs = VFS()
        self.vfs.seed_basic_home(self.home)

        # Пока грузим один урок. Потом легко сделаем выбор урока.
        lesson = load_lesson_json("01_paths.json")

        self.lesson_id = lesson.lesson_id
        self.lesson_title = lesson.title

        self.cwd = lesson.start_cwd
        self._i = 0
        self._correct = 0
        self._attempts = 0

        self._tasks: list[Task] = [self._task_from_raw(t) for t in lesson.tasks]

    def _task_from_raw(self, raw: dict[str, Any]) -> Task:
        # минимальная валидация полей задачи
        for key in ("id", "title", "prompt", "rule", "hint", "success_explain"):
            if key not in raw:
                raise ValueError(f"Task missing required key: {key}")

        rule = raw["rule"]
        if not isinstance(rule, dict) or "kind" not in rule:
            raise ValueError(f"Task {raw.get('id')} has invalid rule")

        return Task(
            id=str(raw["id"]),
            title=str(raw["title"]),
            prompt=str(raw["prompt"]),
            rule=rule,
            hint=str(raw["hint"]),
            success_explain=str(raw["success_explain"]),
        )

    def progress_dict(self) -> dict[str, Any]:
        return {
            "lesson_id": self.lesson_id,
            "lesson_title": self.lesson_title,
            "index": self._i + 1,
            "total": len(self._tasks),
            "correct": self._correct,
            "attempts": self._attempts,
        }

    def current_task(self) -> Task:
        return self._tasks[self._i]

    def hint(self) -> str:
        return self.current_task().hint

    def _advance(self) -> None:
        if self._i < len(self._tasks) - 1:
            self._i += 1

    def submit(self, user_input: str) -> dict[str, Any]:
        self._attempts += 1
        task = self.current_task()

        ok, info, effects = check_command(
            user_input=user_input,
            rule=task.rule,
            cwd=self.cwd,
            home=self.home,
            vfs=self.vfs,
        )

        terminal_lines: list[str] = []
        prompt = f"student@trainer:{self.cwd}$ "
        terminal_lines.append(prompt + user_input)

        code = info.get("code", "ERR")
        msg = info.get("message", "")

        # ВАЖНО: эффекты применяем всегда, даже если goal ещё не достигнут
        if effects.get("set_cwd"):
            self.cwd = effects["set_cwd"]
        if effects.get("last_cmd"):
            self.last_cmd = effects["last_cmd"]

        stdout = effects.get("stdout_lines")
        if stdout:
            terminal_lines.extend(stdout)

        if ok:
            self._correct += 1

            terminal_lines.append("✅ OK")
            terminal_lines.append(task.success_explain)

            self._advance()
            next_task = self.current_task()

            return {
                "ok": True,
                "terminal_lines": terminal_lines,
                "feedback": {"type": "success", "code": code, "text": msg},
                "task": {"id": next_task.id, "title": next_task.title, "prompt": next_task.prompt},
                "cwd": self.cwd,
                "progress": self.progress_dict(),
            }

        # НЕ ok: различаем "цель ещё не достигнута" и реальную ошибку
        if code == "GOAL_NOT_YET":
            terminal_lines.append(f"⚠️ {msg}")
            return {
                "ok": False,
                "terminal_lines": terminal_lines,
                "feedback": {"type": "warn", "code": code, "text": msg},
                "task": {"id": task.id, "title": task.title, "prompt": task.prompt},
                "cwd": self.cwd,
                "progress": self.progress_dict(),
            }

        # реальная ошибка
        terminal_lines.append(f"❌ {msg}")
        return {
            "ok": False,
            "terminal_lines": terminal_lines,
            "feedback": {"type": "error", "code": code, "text": msg},
            "task": {"id": task.id, "title": task.title, "prompt": task.prompt},
            "cwd": self.cwd,
            "progress": self.progress_dict(),
        }
