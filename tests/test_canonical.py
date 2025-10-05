from textwrap import dedent

from sudoku_dlx import from_string, to_string, canonical_form

BASE = dedent(
    """
    53..7....
    6..195...
    .98....6.
    8...6...3
    4..8.3..1
    7...2...6
    .6....28.
    ...419..5
    ....8..79
    """
).strip().replace("\n", "")


def rot90_string(s: str) -> str:
    g = [list(s[r * 9 : (r + 1) * 9]) for r in range(9)]
    out = [["."] * 9 for _ in range(9)]
    for r in range(9):
        for c in range(9):
            out[r][c] = g[9 - 1 - c][r]
    return "".join("".join(row) for row in out)


def relabel_123_to_456(s: str) -> str:
    table = str.maketrans({"1": "4", "2": "5", "3": "6", "4": "1", "5": "2", "6": "3"})
    return s.translate(table)


def swap_bands_string(s: str, order=(1, 0, 2)) -> str:
    rows = [s[i * 9 : (i + 1) * 9] for i in range(9)]
    new_rows = []
    for b in order:
        new_rows.extend(rows[b * 3 : (b + 1) * 3])
    return "".join(new_rows)


def swap_stacks_string(s: str, order=(2, 1, 0)) -> str:
    rows = [list(s[i * 9 : (i + 1) * 9]) for i in range(9)]
    for r in range(9):
        chunks = [rows[r][i * 3 : (i + 1) * 3] for i in range(3)]
        rows[r] = [v for idx in order for v in chunks[idx]]
    return "".join("".join(r) for r in rows)


def swap_rows_in_band_string(s: str, band=1, perm=(2, 0, 1)) -> str:
    rows = [s[i * 9 : (i + 1) * 9] for i in range(9)]
    start = band * 3
    block = rows[start : start + 3]
    new_block = [block[i] for i in perm]
    rows[start : start + 3] = new_block
    return "".join(rows)


def swap_cols_in_stack_string(s: str, stack=0, perm=(1, 2, 0)) -> str:
    rows = [list(s[i * 9 : (i + 1) * 9]) for i in range(9)]
    start = stack * 3
    for r in range(9):
        block = rows[r][start : start + 3]
        rows[r][start : start + 3] = [block[i] for i in perm]
    return "".join("".join(r) for r in rows)


def test_canonical_equal_under_rotation():
    g0 = from_string(BASE)
    g1 = from_string(rot90_string(BASE))
    c0 = canonical_form(g0)
    c1 = canonical_form(g1)
    assert c0 == c1


def test_canonical_equal_under_digit_relabel():
    s2 = relabel_123_to_456(BASE)
    c0 = canonical_form(from_string(BASE))
    c2 = canonical_form(from_string(s2))
    assert c0 == c2


def test_canonical_is_81_chars_and_uses_dots():
    c = canonical_form(from_string(BASE))
    assert len(c) == 81
    assert set(c) <= set("123456789.")


def test_canonical_equal_under_band_and_stack_swaps():
    s_band = swap_bands_string(BASE, order=(1, 0, 2))
    s_stack = swap_stacks_string(BASE, order=(2, 1, 0))
    c0 = canonical_form(from_string(BASE))
    c_band = canonical_form(from_string(s_band))
    c_stack = canonical_form(from_string(s_stack))
    assert c0 == c_band == c_stack


def test_canonical_equal_under_inner_row_col_swaps():
    s_rows = swap_rows_in_band_string(BASE, band=2, perm=(1, 2, 0))
    s_cols = swap_cols_in_stack_string(BASE, stack=1, perm=(2, 0, 1))
    c0 = canonical_form(from_string(BASE))
    c_rows = canonical_form(from_string(s_rows))
    c_cols = canonical_form(from_string(s_cols))
    assert c0 == c_rows == c_cols
