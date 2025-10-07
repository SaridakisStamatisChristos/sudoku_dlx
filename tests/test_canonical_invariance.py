from sudoku_dlx import from_string, to_string, canonical_form

PUZ = (
    "53..7...."
    "6..195..."
    ".98....6."
    "8...6...3"
    "4..8.3..1"
    "7...2...6"
    ".6....28."
    "...419..5"
    "....8..79"
)

def rot180(s: str) -> str:
    return s[::-1]

def swap_rows_in_band(grid, band, r1, r2):
    g = [row[:] for row in grid]
    base = band * 3
    g[base + r1], g[base + r2] = g[base + r2], g[base + r1]
    return g

def test_canonical_invariant_under_basic_isomorphs():
    g = from_string(PUZ)
    c0 = canonical_form(g)
    # rot180 string
    c1 = canonical_form(from_string(rot180(PUZ)))
    assert c1 == c0
    # swap two rows within a band
    g2 = swap_rows_in_band(g, band=0, r1=0, r2=2)
    c2 = canonical_form(g2)
    assert c2 == c0
    # relabel digits 1<->9 on the string
    trans = str.maketrans("123456789", "987654321")
    c3 = canonical_form(from_string(to_string(g).translate(trans)))
    assert c3 == c0
