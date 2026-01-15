from __future__ import annotations

import shlex
from typing import Any

from app.engine.shell import exec_command
from app.engine.asserts import check_asserts
from app.engine.vfs import VFS


def _parse(user_input: str) -> list[str] | None:
    try:
        return shlex.split(user_input.strip())
    except ValueError:
        return None


def _err(code: str, msg: str) -> tuple[bool, dict[str, Any], dict[str, Any]]:
    return False, {"code": code, "message": msg}, {}


def _ok(msg: str, effects: dict[str, Any] | None = None) -> tuple[bool, dict[str, Any], dict[str, Any]]:
    return True, {"code": "OK", "message": msg}, (effects or {})


def check_command(*, user_input: str, rule: dict[str, Any], cwd: str, home: str, vfs: VFS) -> tuple[bool, dict[str, Any], dict[str, Any]]:
    tokens = _parse(user_input)
    if tokens is None:
        return _err("ERR_PARSE", "Не получилось разобрать команду (проверь кавычки).")
    if len(tokens) == 0:
        return _err("ERR_EMPTY", "Пустая команда.")

    cmd = tokens[0].lower()
    args = tokens[1:]

    kind = rule.get("kind")
    if kind != "goal":
        return _err("ERR_UNKNOWN_KIND", "Неизвестный тип задания (rule.kind). Ожидался 'goal'.")

    allowed = rule.get("allowed_cmds", [])
    if not isinstance(allowed, list) or not all(isinstance(x, str) for x in allowed):
        return _err("ERR_BAD_RULE", "Ошибка задания: allowed_cmds должен быть списком строк.")

    allowed_lc = [x.lower() for x in allowed]
    if cmd not in allowed_lc:
        return _err("ERR_CMD_NOT_ALLOWED", f"В этом задании нельзя использовать '{cmd}'. Разрешено: {', '.join(allowed)}")

    expected_cmd = rule.get("expected_cmd")
    if isinstance(expected_cmd, str) and expected_cmd.strip():
        if cmd != expected_cmd.strip().lower():
            return _err("ERR_WRONG_CMD", f"Здесь ожидается команда '{expected_cmd}'.")

    # выполняем команду
    r = exec_command(cmd=cmd, args=args, cwd=cwd, home=home, vfs=vfs)
    if not r.ok:
        return _err(r.code, r.message)

    effects = dict(r.effects)
    if r.stdout_lines:
        effects["stdout_lines"] = r.stdout_lines

    asserts = rule.get("assert", [])
    if not isinstance(asserts, list):
        return _err("ERR_BAD_RULE", "Ошибка задания: assert должен быть списком.")

    # если cd меняет cwd — asserts должны проверяться в новом cwd
    new_cwd = effects.get("set_cwd", cwd)
    last_cmd = effects.get("last_cmd", "")

    ok_goal, msg_goal = check_asserts(
        asserts,
        cwd=new_cwd,
        vfs=vfs,
        last_cmd=last_cmd,
        last_args=effects.get("last_args", []),
    )

    if ok_goal:
        return _ok("Цель достигнута.", effects)

    return False, {"code": "GOAL_NOT_YET", "message": msg_goal}, effects
