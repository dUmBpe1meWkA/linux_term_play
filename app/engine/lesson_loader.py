from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LessonData:
    lesson_id: str
    title: str
    start_cwd: str
    tasks: list[dict[str, Any]]


def load_lesson_json(lesson_filename: str) -> LessonData:
    """
    Загружает JSON-урок из app/content/lessons/<lesson_filename>.
    lesson_filename например: "01_paths.json"
    """
    # lesson_loader.py лежит в app/engine/, поднимаемся в app/
    app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    lesson_path = os.path.join(app_dir, "content", "lessons", lesson_filename)

    with open(lesson_path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    # минимальная валидация
    for key in ("lesson_id", "title", "start_cwd", "tasks"):
        if key not in raw:
            raise ValueError(f"Lesson JSON missing required key: {key}")

    if not isinstance(raw["tasks"], list) or len(raw["tasks"]) == 0:
        raise ValueError("Lesson JSON has empty tasks list")

    return LessonData(
        lesson_id=str(raw["lesson_id"]),
        title=str(raw["title"]),
        start_cwd=str(raw["start_cwd"]),
        tasks=list(raw["tasks"]),
    )
