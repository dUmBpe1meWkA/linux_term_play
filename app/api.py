from __future__ import annotations
from dataclasses import asdict
from app.engine.session import Session
from app.storage.save import load_save, write_save, delete_save, do_has_save


class AppAPI:
    """
    Этот объект становится доступным в JS как window.pywebview.api.*
    (pywebview автоматически связывает методы).
    """

    def __init__(self) -> None:
        self.session = None

    def get_task(self) -> dict:
        if self.session is None:
            self.session = Session(lesson_id="01_paths")
        task = self.session.current_task()
        return {
            "task": asdict(task),
            "cwd": self.session.cwd,
            "progress": self.session.progress_dict(),
        }

    def submit_command(self, command: str) -> dict:
        """
        Принять команду от пользователя, проверить её, вернуть:
        - строки для вывода в "терминал"
        - фидбек
        - возможно следующее задание
        """
        result = self.session.submit(command)
        write_save(self.session.lesson_id, self.session.to_dict())
        return result

    def get_hint(self) -> dict:
        """Вернуть подсказку по текущему заданию."""
        hint = self.session.hint()
        return {"hint": hint}

    def reset_progress(self, lesson_id: str = "01_paths") -> dict:
        delete_save(lesson_id)
        self.session = Session(lesson_id=lesson_id)
        write_save(lesson_id, self.session.to_dict())
        return self.get_task()

    def start_new(self, lesson_id: str) -> dict:
        delete_save(lesson_id)
        self.session = Session(lesson_id=lesson_id)
        write_save(lesson_id, self.session.to_dict())
        return self.get_task()

    def continue_game(self, lesson_id: str) -> dict:
        saved = load_save(lesson_id)
        if saved:
            self.session = Session(lesson_id=lesson_id)
            self.session.from_dict(saved)
        else:
            # если сохранения нет — начинаем заново этот урок
            self.session = Session(lesson_id=lesson_id)
            write_save(lesson_id, self.session.to_dict())
        return self.get_task()

    def has_save(self, lesson_id: str) -> dict:
        return {"has_save": do_has_save(lesson_id)}

    def list_lessons(self) -> dict:
        # пока простой список, позже можно читать из папки
        return {
            "lessons": [
                {"id": "01_paths", "title": "01 — Пути и навигация"},
                {"id": "02_files", "title": "02 — Файлы и папки"},
            ]
        }
