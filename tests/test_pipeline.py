"""End-to-end scenarios (test cases TC-P*)."""

import pytest

from tests.conftest import read_sample

# scenario, expected accepted profiles
SCENARIOS = [
    ("wednesday_addams.txt", {"FULL_STACK_DEVELOPER"}),
    ("mary_jane_watson.txt", {"MACHINE_LEARNING_ENGINEER"}),
    ("peter_parker.txt", {"DEVOPS_ENGINEER"}),
    ("gwen_stacy.txt", {"DATA_ANALYST"}),
    ("bruce_wayne.txt", {"FULL_STACK_DEVELOPER", "DEVOPS_ENGINEER"}),
    ("clark_kent.txt", set()),
    ("diana_prince.txt", {"FULL_STACK_DEVELOPER"}),
    ("tony_stark.txt", {"MACHINE_LEARNING_ENGINEER"}),
]


@pytest.mark.parametrize("sample,expected", SCENARIOS)
def test_scenarios(lens, sample, expected):
    result = lens.analyze(read_sample(sample))
    assert set(result.accepted_profiles) == expected


def test_outputs_are_saved(lens, tmp_path):
    result = lens.analyze(read_sample("wednesday_addams.txt"))
    paths = result.save(tmp_path, "wednesday")
    for p in paths.values():
        assert p.exists() and p.stat().st_size > 0


def test_resume_without_skills(lens):
    result = lens.analyze("John Smith\njohn@smith.com\nI like hiking.")
    assert result.accepted_profiles == []
    assert result.model.candidate.name == "John Smith"


def test_cli(tmp_path, capsys):
    from resumelens.cli import main
    from tests.conftest import SAMPLES
    assert main(["analyze", str(SAMPLES / "wednesday_addams.txt"), "--out", str(tmp_path)]) == 0
    assert "ACCEPTED" in capsys.readouterr().out
    assert main(["validate", str(SAMPLES / "invalid" / "syntax_missing_semicolon.resume")]) == 2
    assert main(["validate", str(SAMPLES / "invalid" / "semantic_duplicated_skill.resume")]) == 3
