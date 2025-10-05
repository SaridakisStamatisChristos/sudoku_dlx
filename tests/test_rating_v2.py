from sudoku_dlx import (
    rate, from_string, to_string, solve, generate, canonical_form
)

BASE = (
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

def test_rate_bounds():
    # solvable puzzle
    g = from_string(BASE)
    s = rate(g)
    assert 0.0 <= s <= 10.0
    # unsolvable (contradiction): duplicate in a row
    bad = [row[:] for row in g]
    bad[0][0] = 5
    bad[0][1] = 5
    assert rate(bad) == 10.0

def test_rate_isomorphism_stability():
    g = from_string(BASE)
    s0 = rate(g)
    # Rotate 90° via canonical round-trip to ensure isomorphic grid
    can = canonical_form(g)
    s1 = rate(from_string(can))
    assert abs(s0 - s1) < 1e-6

def test_rate_monotonic_with_more_givens():
    # Generate a base puzzle and a denser variant by adding correct digits
    p = generate(seed=123, target_givens=34, minimal=False, symmetry="none")
    res = solve([row[:] for row in p])
    assert res is not None
    # Fill up to +5 blanks with solution digits to make it easier
    added = 0
    denser = [row[:] for row in p]
    for r in range(9):
        for c in range(9):
            if denser[r][c] == 0 and added < 5:
                denser[r][c] = res.grid[r][c]
                added += 1
    s_lo = rate(p)
    s_hi = rate(denser)
    assert s_lo >= s_hi - 1e-6  # denser (more givens) should not rate harder
