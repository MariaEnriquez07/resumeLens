"""Smoke tests of the Streamlit interface (skipped if Streamlit is missing)."""

from pathlib import Path

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

APP = str(Path(__file__).resolve().parents[1] / "app.py")


def test_app_runs_pipeline():
    at = AppTest.from_file(APP, default_timeout=60).run()
    assert not at.exception
    at.selectbox[0].select("wednesday_addams.txt").run()
    at.button[0].click().run()
    assert not at.exception
    assert any("ACCEPTED" in e.label for e in at.expander)


def test_app_validates_specification():
    at = AppTest.from_file(APP, default_timeout=60).run()
    at.button[1].click().run()
    assert not at.exception
    assert at.success and "Valid profile" in at.success[0].value