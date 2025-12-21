from __future__ import annotations

from dataclasses import asdict

from app.engine.session import Session


class AppAPI:
    """
    Этот объект становится доступным в JS как window.pywebview.api.*
    (pywebview автоматически связывает методы).
    """

    def __init__(self) -> None:
        self.session = Session()

    def get_task(self) -> dict:
        """Вернуть текущее задание (для показа в UI)."""
        task = self.session.current_task()
        return {"task": asdict(task), "cwd": self.session.cwd, "progress": self.session.progress_dict()}

    def submit_command(self, command: str) -> dict:
        """
        Принять команду от пользователя, проверить её, вернуть:
        - строки для вывода в "терминал"
        - фидбек
        - возможно следующее задание
        """
        result = self.session.submit(command)
        return result

    def get_hint(self) -> dict:
        """Вернуть подсказку по текущему заданию."""
        hint = self.session.hint()
        return {"hint": hint}
