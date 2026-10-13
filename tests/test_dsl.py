"""Stage 4 — context-free grammar with textX (test cases TC-G*)."""

from pathlib import Path

import pytest

from resumelens import dsl
from resumelens.render import to_html
from tests.conftest import SAMPLES

INVALID = sorted((SAMPLES / "invalid").glob("*.resume"))


# TC-G01 — valid specifications
@pytest.mark.parametrize("name", ["valid_minimal.resume", "valid_wednesday_addams.resume"])
def test_valid_files(name):
    model = dsl.parse_file(SAMPLES / name)
    assert model.candidate.name
    assert model.classification.results


def test_structure_of_model():
    model = dsl.parse_file(SAMPLES / "valid_minimal.resume")
    assert [g.category for g in model.skills.groups] == ["LANGUAGES", "FRAMEWORKS",
                                                         "DATABASES", "TOOLS"]
    r = model.classification.results[0]
    assert (r.profile, r.status, r.automaton) == ("FULL_STACK_DEVELOPER", "ACCEPTED", "DFA")


# TC-G02 — lexical and syntactic violations
@pytest.mark.parametrize("path", [p for p in INVALID if p.name.startswith(("lexical", "syntax"))],
                         ids=lambda p: p.stem)
def test_syntax_errors(path):
    with pytest.raises(dsl.TextXSyntaxError):
        dsl.parse_file(path)


# TC-G03 — semantic violations (context-sensitive rules)
@pytest.mark.parametrize("path", [p for p in INVALID if p.name.startswith("semantic")],
                         ids=lambda p: p.stem)
def test_semantic_errors(path):
    with pytest.raises(dsl.TextXSemanticError):
        dsl.parse_file(path)


def test_there_are_invalid_cases():
    assert len(INVALID) == 8


# TC-G04 — repeated elements
def test_repeated_education_and_jobs(lens):
    text = (SAMPLES / "tony_stark.txt").read_text()
    model = lens.analyze(text).model
    assert len(model.education.records) == 2
    assert len(model.experience.jobs) == 2


# TC-G05 — HTML visualization
def test_html():
    model = dsl.parse_file(SAMPLES / "valid_minimal.resume")
    html = to_html(model)
    assert html.startswith("<!DOCTYPE html>") and "Test Candidate" in html
    assert "Full Stack Developer" in html and "JAVASCRIPT" in html


def test_html_escapes_text():
    text = Path(SAMPLES / "valid_minimal.resume").read_text().replace(
        "Test Candidate", "<script>x</script>")
    assert "<script>x" not in to_html(dsl.parse(text))