from __future__ import annotations

from typing import Any
import posixpath
from app.engine.vfs import VFS


def _abs(path: str, cwd: str) -> str:
    if not path.startswith("/"):
        return posixpath.normpath(posixpath.join(cwd, path))
    return posixpath.normpath(path)


def check_asserts(assert_list: list[dict[str, Any]], *, cwd: str, vfs: VFS, last_cmd: str) -> tuple[bool, str]:
    if not isinstance(assert_list, list):
        return False, "Ошибка задания: assert должен быть списком."

    for a in assert_list:
        if not isinstance(a, dict):
            return False, "Ошибка задания: некорректный assert."

        t = a.get("type")
        if not isinstance(t, str):
            return False, "Ошибка задания: некорректный assert."

        if t == "exists_dir":
            path = a.get("path")
            if not isinstance(path, str):
                return False, "Ошибка задания: exists_dir без path."
            p = _abs(path, cwd)
            if not vfs.exists(p) or not vfs.is_dir(p):
                return False, f"Пока нет директории: {p}"

        elif t == "exists_file":
            path = a.get("path")
            if not isinstance(path, str):
                return False, "Ошибка задания: exists_file без path."
            p = _abs(path, cwd)
            if not vfs.exists(p) or not vfs.is_file(p):
                return False, f"Пока нет файла: {p}"

        elif t == "cwd_is":
            expected = a.get("value")
            if not isinstance(expected, str):
                return False, "Ошибка задания: cwd_is без value."
            if posixpath.normpath(cwd) != posixpath.normpath(expected):
                return False, f"Нужно оказаться в: {expected}"

        elif t == "last_cmd_is":
            expected = a.get("value")
            if not isinstance(expected, str):
                return False, "Ошибка задания: last_cmd_is без value."
            if last_cmd != expected:
                return False, f"Сейчас ожидается команда: {expected}"

        else:
            return False, f"Неизвестный assert.type: {t}"

    return True, "Цель достигнута."
