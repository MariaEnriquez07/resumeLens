import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SAMPLES = ROOT / "samples"


@pytest.fixture(scope="session")
def lens():
    from resumelens.pipeline import ResumeLens
    return ResumeLens()


@pytest.fixture(scope="session")
def normalizer():
    from resumelens.normalization import Normalizer
    return Normalizer()


def read_sample(name: str) -> str:
    return (SAMPLES / name).read_text(encoding="utf-8")