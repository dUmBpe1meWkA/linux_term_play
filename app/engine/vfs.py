from __future__ import annotations

from dataclasses import dataclass
import posixpath


@dataclass
class Node:
    name: str
    kind: str  # "dir" | "file"
    children: dict[str, "Node"] | None = None


class VFS:
    """
    Мини-VFS (виртуальная файловая система) только для обучения.
    Никаких реальных файлов на диске.
    """

    def __init__(self) -> None:
        self.root = Node(name="/", kind="dir", children={})

    def seed_basic_home(self, home: str) -> None:
        """
        Создаём базовую структуру: /home/student и пару папок.
        """
        self.ensure_dir("/home")
        self.ensure_dir(home)
        self.ensure_dir(posixpath.join(home, "projects"))
        self.ensure_dir(posixpath.join(home, "downloads"))
        self.ensure_file(posixpath.join(home, "readme.txt"))

    # ---------- path helpers ----------
    def _split(self, path: str) -> list[str]:
        p = posixpath.normpath(path)
        if p == "/":
            return []
        return [x for x in p.split("/") if x]

    def _walk(self, path: str) -> Node | None:
        """
        Вернуть узел по абсолютному path или None.
        """
        parts = self._split(path)
        cur = self.root
        for part in parts:
            if cur.kind != "dir" or cur.children is None:
                return None
            cur = cur.children.get(part)
            if cur is None:
                return None
        return cur

    def exists(self, path: str) -> bool:
        return self._walk(path) is not None

    def is_dir(self, path: str) -> bool:
        n = self._walk(path)
        return (n is not None) and (n.kind == "dir")

    def is_file(self, path: str) -> bool:
        n = self._walk(path)
        return (n is not None) and (n.kind == "file")

    # ---------- mutating ops ----------
    def ensure_dir(self, path: str) -> None:
        """
        Создать директорию (и родителей), как mkdir -p.
        """
        parts = self._split(path)
        cur = self.root
        for part in parts:
            if cur.children is None:
                cur.children = {}
            nxt = cur.children.get(part)
            if nxt is None:
                nxt = Node(name=part, kind="dir", children={})
                cur.children[part] = nxt
            else:
                if nxt.kind != "dir":
                    raise ValueError(f"Cannot create dir '{path}': '{part}' is a file")
            cur = nxt

    def ensure_file(self, path: str) -> None:
        """
        Создать файл (как touch): создаёт родителей, файл создаёт если нет.
        """
        parent = posixpath.dirname(posixpath.normpath(path))
        name = posixpath.basename(posixpath.normpath(path))
        if name in ("", "/", ".", ".."):
            raise ValueError("Bad file name")

        self.ensure_dir(parent)

        pnode = self._walk(parent)
        assert pnode and pnode.kind == "dir" and pnode.children is not None

        existing = pnode.children.get(name)
        if existing is None:
            pnode.children[name] = Node(name=name, kind="file", children=None)
        else:
            if existing.kind != "file":
                raise ValueError("Cannot touch: target is a directory")

    def mkdir(self, path: str) -> None:
        """
        mkdir без -p: падает если уже существует.
        """
        p = posixpath.normpath(path)
        if self.exists(p):
            raise ValueError("File exists")
        self.ensure_dir(p)

    def touch(self, path: str) -> None:
        self.ensure_file(path)

    def list_dir(self, path: str) -> list[str]:
        """
        Возвращает список имён в директории.
        """
        n = self._walk(path)
        if n is None:
            raise ValueError("No such file or directory")
        if n.kind != "dir" or n.children is None:
            raise ValueError("Not a directory")
        return sorted(n.children.keys())
