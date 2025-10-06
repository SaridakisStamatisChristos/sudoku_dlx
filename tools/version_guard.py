"""
Fail the build if the Git tag (refs/tags/vX.Y.Z) does not match sudoku_dlx.__version__.
Usage (CI): python tools/version_guard.py --tag "$GITHUB_REF_NAME"
"""
from __future__ import annotations
import argparse, re, sys

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True, help="git tag name, e.g. v0.2.1")
    ns = ap.parse_args()
    tag = ns.tag.strip()
    m = re.fullmatch(r"v(\d+\.\d+\.\d+)", tag)
    if not m:
        print(f"[version_guard] Not a release tag: {tag}", file=sys.stderr)
        return 2
    tag_ver = m.group(1)
    try:
        import sudoku_dlx as pkg
    except Exception as e:
        print(f"[version_guard] Failed to import sudoku_dlx: {e}", file=sys.stderr)
        return 3
    code_ver = getattr(pkg, "__version__", None)
    if code_ver is None:
        print("[version_guard] sudoku_dlx.__version__ missing", file=sys.stderr)
        return 4
    if code_ver != tag_ver:
        print(f"[version_guard] Version mismatch: tag v{tag_ver} != code {code_ver}", file=sys.stderr)
        return 5
    print(f"[version_guard] OK: tag v{tag_ver} == code {code_ver}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
