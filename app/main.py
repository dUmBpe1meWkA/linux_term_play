from __future__ import annotations

import os
import webview

from app.api import AppAPI


def _abs_path(*parts: str) -> str:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root, *parts)


def main() -> None:
    api = AppAPI()

    index_file = _abs_path("ui", "index.html")
    window = webview.create_window(
        title="Linux Trainer",
        url=index_file,
        js_api=api,
        width=1100,
        height=720,
        resizable=True,
    )

    webview.start(debug=False)


if __name__ == "__main__":
    main()
