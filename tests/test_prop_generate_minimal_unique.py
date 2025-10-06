from sudoku_dlx import generate, count_solutions


def _is_minimal_strict(g) -> bool:
    for r in range(9):
        for c in range(9):
            if g[r][c] == 0:
                continue
            keep = g[r][c]
            g[r][c] = 0
            uniq = count_solutions(g, limit=2) == 1
            g[r][c] = keep
            if uniq:
                return False
    return True


def test_generate_minimal_unique_fast_settings():
    # modest givens to keep runtime under control in CI
    for seed in [5, 9]:
        p = generate(seed=seed, target_givens=36, minimal=True, symmetry="none")
        assert count_solutions(p, limit=2) == 1
        assert _is_minimal_strict(p)
