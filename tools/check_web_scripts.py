from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
import subprocess
import tempfile


class _ScriptCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._capture = False
        self._parts: list[str] = []
        self.scripts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "script":
            return
        attr_map = dict(attrs)
        self._capture = "src" not in attr_map
        self._parts = []

    def handle_data(self, data: str) -> None:
        if self._capture:
            self._parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._capture:
            script = "".join(self._parts).strip()
            if script:
                self.scripts.append(script)
            self._capture = False
            self._parts = []


def _node_check(path: Path) -> None:
    subprocess.run(["node", "--check", str(path)], check=True)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    _node_check(root / "web" / "worker.js")

    with tempfile.TemporaryDirectory(prefix="sudoku-web-check-") as tmp:
        tmp_path = Path(tmp)
        for html_name in ("index.html", "visualizer.html"):
            source = (root / "web" / html_name).read_text(encoding="utf-8")
            parser = _ScriptCollector()
            parser.feed(source)
            if not parser.scripts:
                raise SystemExit(f"no inline script found in web/{html_name}")
            for index, script in enumerate(parser.scripts):
                script_path = tmp_path / f"{html_name}.{index}.js"
                script_path.write_text(script, encoding="utf-8")
                _node_check(script_path)

    print("browser JavaScript syntax ok")


if __name__ == "__main__":
    main()
