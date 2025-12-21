from __future__ import annotations

import posixpath


def normalize_path(path: str, *, cwd: str, home: str) -> str:
    """
    Нормализация POSIX-пути (как в Linux), без реальной ФС:
    - ~ разворачиваем в home
    - относительные пути считаем от cwd
    - убираем лишние /, . и ..
    - убираем конечный / (кроме корня)
    """
    p = path.strip()

    # ~ или ~/...
    if p == "~":
        p = home
    elif p.startswith("~/"):
        p = posixpath.join(home, p[2:])

    # абсолютный/относительный
    if not p.startswith("/"):
        p = posixpath.join(cwd, p)

    # нормализуем . и ..
    p = posixpath.normpath(p)

    # normpath уже убирает конечные слеши. "/": остаётся "/"
    return p


def split_flags(args: list[str]) -> tuple[list[str], list[str]]:
    """
    Очень простой разбор аргументов для команд типа ls:
    - всё, что начинается с '-' считаем флагом
    - остальное — позиционные аргументы

    Важно: это MVP-логика. Позже можно сделать полноценнее.
    """
    flags: list[str] = []
    pos: list[str] = []
    for a in args:
        if a.startswith("-") and len(a) > 1:
            flags.append(a)
        else:
            pos.append(a)
    return flags, pos
