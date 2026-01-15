from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import posixpath

from app.engine.normalize import normalize_path, split_flags
from app.engine.vfs import VFS


@dataclass
class ExecResult:
    ok: bool
    code: str
    message: str
    stdout_lines: list[str]
    effects: dict[str, Any]


def exec_command(*, cmd: str, args: list[str], cwd: str, home: str, vfs: VFS) -> ExecResult:
    cmd = cmd.lower()

    # ---- pwd ----
    if cmd == "pwd":
        if args:
            return ExecResult(False, "ERR_UNEXPECTED_ARGS", "pwd не принимает аргументы.", [], {})
        return ExecResult(True, "OK", "OK", [cwd], {"last_cmd": "pwd", "last_args": args})

    # ---- ls ----
    if cmd == "ls":
        flags, positionals = split_flags(args)
        if positionals:
            return ExecResult(False, "ERR_UNEXPECTED_PATH",
                              "В MVP ls работает без пути: просто ls или ls -l.", [], {})

        names = vfs.list_dir(cwd)

        if "-l" in flags:
            lines = []
            for n in names:
                p = posixpath.normpath(posixpath.join(cwd, n))
                lines.append(("drwxr-xr-x  " if vfs.is_dir(p) else "-rw-r--r--  ") + n)
            return ExecResult(True, "OK", "OK", lines, {"last_cmd": "ls", "last_args": args})
        else:
            return ExecResult(True, "OK", "OK",
                              ["  ".join(names)] if names else [""],
                              {"last_cmd": "ls", "last_args": args})

    # ---- cd ----
    if cmd == "cd":
        if len(args) == 0:
            return ExecResult(False, "ERR_MISSING_ARG", "После cd нужно указать путь.", [], {})
        if len(args) > 1:
            return ExecResult(False, "ERR_TOO_MANY_ARGS", "cd принимает ровно один аргумент.", [], {})

        target = normalize_path(args[0], cwd=cwd, home=home)

        if not vfs.exists(target):
            return ExecResult(False, "ERR_NO_SUCH_DIR", f"Такой директории нет: {target}.", [], {})
        if not vfs.is_dir(target):
            return ExecResult(False, "ERR_NOT_DIR", f"Это не директория: {target}.", [], {})

        return ExecResult(True, "OK", "OK", [], {"set_cwd": target, "last_cmd": "cd", "last_args": args})

    # ---- mkdir ----
    if cmd == "mkdir":
        if len(args) == 0:
            return ExecResult(False, "ERR_MISSING_ARG", "После mkdir нужно указать имя директории.", [], {})
        if len(args) > 1:
            return ExecResult(False, "ERR_TOO_MANY_ARGS", "В MVP mkdir создаёт одну директорию.", [], {})

        target = normalize_path(args[0], cwd=cwd, home=home)
        try:
            vfs.mkdir(target)
        except ValueError:
            return ExecResult(False, "ERR_EXISTS", "Такая директория уже существует.", [], {})
        return ExecResult(True, "OK", "OK", [], {"last_cmd": "mkdir", "last_args": args})

    # ---- touch ----
    if cmd == "touch":
        if len(args) == 0:
            return ExecResult(False, "ERR_MISSING_ARG", "После touch нужно указать имя файла.", [], {})
        if len(args) > 1:
            return ExecResult(False, "ERR_TOO_MANY_ARGS", "В MVP touch создаёт один файл.", [], {})

        target = normalize_path(args[0], cwd=cwd, home=home)
        try:
            vfs.touch(target)
        except ValueError as e:
            return ExecResult(False, "ERR_TOUCH", str(e), [], {})
        return ExecResult(True, "OK", "OK", [], {"last_cmd": "touch", "last_args": args})

    return ExecResult(False, "ERR_UNKNOWN_CMD", f"Команда '{cmd}' пока не поддерживается.", [], {})
