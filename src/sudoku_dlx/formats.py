from __future__ import annotations

from typing import Iterable, List, Optional
import csv
import json
import pathlib


# All “grid strings” are 81 chars, dots for blanks.

def _strip_grid_line(s: str) -> str:
    return "".join(ch for ch in s.strip() if not ch.isspace())


def _is_81(s: str) -> bool:
    return len(s) == 81


def detect_format(path: str) -> str:
    p = pathlib.Path(path)
    ext = p.suffix.lower().lstrip(".")
    if ext in {"txt", "sdk"}:
        return "txt"
    if ext in {"csv"}:
        return "csv"
    if ext in {"jsonl", "ndjson"}:
        return "jsonl"
    # default: try txt
    return "txt"


def read_grids(path: str, fmt: Optional[str] = None) -> List[str]:
    fmt = fmt or detect_format(path)
    p = pathlib.Path(path)
    if fmt == "txt":
        out: List[str] = []
        for line in p.read_text(encoding="utf-8").splitlines():
            s = _strip_grid_line(line)
            if not s:
                continue
            if not _is_81(s):
                raise ValueError(f"bad grid length (expected 81): {s!r}")
            out.append(s)
        return out
    if fmt == "csv":
        out: List[str] = []
        with p.open("r", encoding="utf-8", newline="") as f:
            sniffer = csv.Sniffer()
            text = f.read()
            f.seek(0)
            try:
                dialect = sniffer.sniff(text)
            except Exception:
                dialect = csv.excel
            reader = csv.DictReader(f, dialect=dialect)
            if reader.fieldnames is None or len(reader.fieldnames) == 0:
                raise ValueError("CSV missing header row")
            field = "grid" if "grid" in reader.fieldnames else reader.fieldnames[0]
            for row in reader:
                cell = row.get(field, "")
                s = _strip_grid_line(cell)
                if _is_81(s):
                    out.append(s)
        return out
    if fmt == "jsonl":
        out: List[str] = []
        with p.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                obj = json.loads(line)
                s = _strip_grid_line(obj.get("grid", ""))
                if _is_81(s):
                    out.append(s)
        return out
    raise ValueError(f"unknown format: {fmt}")


def write_grids(path: str, grids: Iterable[str], fmt: Optional[str] = None) -> None:
    fmt = fmt or detect_format(path)
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if fmt == "txt":
        p.write_text("\n".join(grids) + "\n", encoding="utf-8")
        return
    if fmt == "csv":
        with p.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["grid"])
            for s in grids:
                writer.writerow([s])
        return
    if fmt == "jsonl":
        with p.open("w", encoding="utf-8") as f:
            for s in grids:
                f.write(json.dumps({"grid": s}, separators=(",", ":")) + "\n")
        return
    raise ValueError(f"unknown format: {fmt}")
