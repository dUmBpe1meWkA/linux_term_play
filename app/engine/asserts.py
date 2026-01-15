from __future__ import annotations

import posixpath
from app.engine.vfs import VFS


def _abs(path: str, cwd: str) -> str:
    if not path.startswith("/"):
        return posixpath.normpath(posixpath.join(cwd, path))
    return posixpath.normpath(path)


def check_asserts(assert_list, *, cwd, vfs: VFS, last_cmd: str, last_args: list[str]):
    problems: list[str] = []

    if not isinstance(assert_list, list):
        return False, "Ошибка задания: assert должен быть списком."

    for a in assert_list:
        if not isinstance(a, dict):
            problems.append("Некорректный assert.")
            continue

        t = a.get("type")
        if not isinstance(t, str):
            problems.append("Некорректный assert (нет type).")
            continue

        if t == "exists_dir":
            path = a.get("path")
            if not isinstance(path, str):
                problems.append("exists_dir без path")
                continue
            p = _abs(path, cwd)
            if not vfs.exists(p) or not vfs.is_dir(p):
                problems.append(f"Создай директорию: {p}")

        elif t == "exists_file":
            path = a.get("path")
            if not isinstance(path, str):
                problems.append("exists_file без path")
                continue
            p = _abs(path, cwd)
            if not vfs.exists(p) or not vfs.is_file(p):
                problems.append(f"Создай файл: {p}")

        elif t == "cwd_is":
            expected = a.get("value")
            if not isinstance(expected, str):
                problems.append("cwd_is без value")
                continue
            if posixpath.normpath(cwd) != posixpath.normpath(expected):
                problems.append(f"Перейди в: {expected}")

        elif t == "last_cmd_is":
            expected = a.get("value")
            if not isinstance(expected, str):
                problems.append("last_cmd_is без value")
                continue
            if last_cmd != expected:
                problems.append(f"Используй команду: {expected}")

        elif t == "has_flag":
            flag = a.get("value")
            if not isinstance(flag, str):
                problems.append("has_flag без value")
                continue
            if flag not in last_args:
                problems.append(f"Добавь флаг {flag}")

        else:
            problems.append(f"Неизвестный assert.type: {t}")

    if problems:
        return False, "Осталось:\n- " + "\n- ".join(problems)

    return True, "Цель достигнута."
