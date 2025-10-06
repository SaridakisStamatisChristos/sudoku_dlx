import pytest
from hypothesis import given, settings, strategies as st
from sudoku_dlx import from_string, canonical_form

# Keep canonical check cheap: compare original vs rot180 isomorph


@pytest.mark.prop
@settings(max_examples=10, deadline=None)
@given(st.lists(st.sampled_from(list(".123456789")), min_size=81, max_size=81))
def test_canonical_invariant_under_rot180(xs):
    s = "".join(xs)
    g = from_string(s)
    # build rot180 string
    s2 = "".join(s[::-1])
    g2 = from_string(s2)
    assert canonical_form(g) == canonical_form(g2)
