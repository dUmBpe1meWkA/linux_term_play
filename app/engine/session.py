from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

from app.engine.vfs import VFS
from app.engine.checker import check_command


@dataclass(frozen=True)
class Task:
    id: str
    title: str
    prompt: str
    rule: dict[str, Any]
    hint: str
    success_explain: str


LESSONS_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "content", "lessons"))


def load_lesson(lesson_id: str) -> tuple[str, str, str, list[Task]]:
    path = os.path.join(LESSONS_DIR, f"{lesson_id}.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # схема: lesson_id, title, start_cwd, tasks
    lid = str(data["lesson_id"])
    title = str(data.get("title", lid))
    start_cwd = str(data.get("start_cwd", "/home/student"))

    tasks: list[Task] = []
    for t in data.get("tasks", []):
        tasks.append(Task(
            id=str(t["id"]),
            title=str(t["title"]),
            prompt=str(t["prompt"]),
            rule=t["rule"],
            hint=str(t.get("hint", "")),
            success_explain=str(t.get("success_explain", "")),
        ))

    if not tasks:
        raise ValueError(f"Lesson {lesson_id} has empty tasks list")

    return lid, title, start_cwd, tasks


class Session:
    def __init__(self, lesson_id: str = "01_paths") -> None:
        self.home = "/home/student"
        self.vfs = VFS()
        self.vfs.seed_basic_home(self.home)

        self.last_args: list[str] = []
        self.last_cmd = ""

        self.lesson_id, self.lesson_title, self.cwd, self._tasks = load_lesson(lesson_id)

        self._i = 0
        self._correct = 0
        self._attempts = 0


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
        if effects and effects.get("last_args") is not None:
            self.last_args = effects["last_args"]

        terminal_lines: list[str] = []
        # prompt = f"student@trainer:{self.cwd}$ "
        # terminal_lines.append(prompt + user_input)

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

    def to_dict(self) -> dict:
        return {
            "lesson_id": self.lesson_id,
            "cwd": self.cwd,
            "task_index": self._i,
            "attempts": self._attempts,
            "correct": self._correct,
            "vfs": self.vfs.to_dict(),
        }

    def from_dict(self, data: dict) -> None:
        saved_lesson_id = data.get("lesson_id")
        if saved_lesson_id and saved_lesson_id != self.lesson_id:
            return
        self.cwd = data.get("cwd", self.cwd)

        i = int(data.get("task_index", 0))
        if i < 0:
            i = 0
        if i >= len(self._tasks):
            i = len(self._tasks) - 1
        self._i = i

        self._attempts = int(data.get("attempts", 0))
        self._correct = int(data.get("correct", 0))

        vfs_data = data.get("vfs")
        if isinstance(vfs_data, dict):
            self.vfs.from_dict(vfs_data)
