from pathlib import Path
import json

SAVE_DIR = Path("appdata")
SAVE_DIR.mkdir(exist_ok=True)


def _save_path(lesson_id: str) -> Path:
    return SAVE_DIR / f"save_{lesson_id}.json"


def load_save(lesson_id: str) -> dict | None:
    p = _save_path(lesson_id)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def write_save(lesson_id: str, data: dict) -> None:
    p = _save_path(lesson_id)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def delete_save(lesson_id: str) -> None:
    p = _save_path(lesson_id)
    if p.exists():
        p.unlink()


def do_has_save(lesson_id: str) -> bool:
    return _save_path(lesson_id).exists()
