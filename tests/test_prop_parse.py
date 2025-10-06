import pytest
from hypothesis import given, settings, strategies as st
from sudoku_dlx import from_string, to_string

# Allowed characters for parser (blanks + digits)
chars = st.sampled_from(list(".0123456789"))


@pytest.mark.prop
@settings(max_examples=30, deadline=None)
@given(st.lists(chars, min_size=81, max_size=81))
def test_from_to_string_round_trip_preserves_clues(xs):
    s = "".join(xs)
    g = from_string(s)
    s2 = to_string(g)
    assert len(s2) == 81
    # any non-blank in input stays same in output at same index
    for i, ch in enumerate(s):
        if ch in "123456789":
            assert s2[i] == ch
        else:
            assert s2[i] == "."  # blanks normalize to '.'


# Mix in arbitrary whitespace; parser should ignore it
ws = st.text(alphabet=st.sampled_from(list(" \t\r\n")), min_size=0, max_size=20)


@pytest.mark.prop
@settings(max_examples=20, deadline=None)
@given(st.lists(chars, min_size=81, max_size=81), ws, ws)
def test_parser_ignores_whitespace(xs, pre, post):
    s = pre + "".join(xs) + post
    g = from_string(s)
    assert len(to_string(g)) == 81
