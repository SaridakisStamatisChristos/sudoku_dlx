from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

if os.getenv("USE_HYPOTHESIS_STUB") == "1" or importlib.util.find_spec("hypothesis") is None:
    stub_path = Path(__file__).parent / "_stubs"
    stub_str = str(stub_path)
    if stub_str not in sys.path:
        sys.path.insert(0, stub_str)

from _pytest.config import Config
from _pytest.config.argparsing import Parser
from hypothesis import HealthCheck, Phase, settings  # type: ignore

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if SRC_PATH.is_dir():
    src_str = str(SRC_PATH)
    if src_str not in sys.path:
        sys.path.insert(0, src_str)

    existing = os.environ.get("PYTHONPATH")
    if existing:
        if src_str not in existing.split(os.pathsep):
            os.environ["PYTHONPATH"] = os.pathsep.join([src_str, existing])
    else:
        os.environ["PYTHONPATH"] = src_str

_HAS_PYTEST_COV = importlib.util.find_spec("pytest_cov") is not None


def pytest_addoption(parser: Parser) -> None:
    """Register no-op coverage flags when pytest-cov is unavailable."""

    if _HAS_PYTEST_COV:
        return

    group = parser.getgroup("cov (missing plugin)")
    group.addoption(
        "--cov",
        action="append",
        dest="cov",
        default=[],
        metavar="PATH",
        help="coverage reporting requires pytest-cov; option accepted but ignored.",
    )
    group.addoption(
        "--cov-report",
        action="append",
        dest="cov_report",
        default=[],
        help="coverage reporting requires pytest-cov; option accepted but ignored.",
    )


def pytest_configure(config: Config) -> None:
    if _HAS_PYTEST_COV:
        return

    if getattr(config.option, "cov", None) or getattr(config.option, "cov_report", None):
        config.issue_config_time_warning(
            "pytest-cov is not installed; coverage options are ignored.",
            stacklevel=2,
        )


# Register lean Hypothesis profiles and select via env HYPOTHESIS_PROFILE
# - "ci": very small example counts, no database, suppress flaky health checks.
# - "nightly": larger runs with shrinking, no deadlines.
settings.register_profile(
    "ci",
    max_examples=8,
    phases=(Phase.generate, Phase.shrink),
    deadline=None,
    derandomize=True,
    suppress_health_check=[
        HealthCheck.too_slow,
        HealthCheck.filter_too_much,
        HealthCheck.data_too_large,
    ],
    database=None,
)
settings.register_profile(
    "nightly",
    max_examples=200,
    phases=(Phase.generate, Phase.shrink),
    deadline=None,
)
settings.load_profile(os.getenv("HYPOTHESIS_PROFILE", "default"))
