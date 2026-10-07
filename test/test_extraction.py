"""Stage 1 — regular expressions (test cases TC-E*)."""

import re

import pytest

from resumelens.catalog import LEXICON
from resumelens.extraction import (EMAIL_RE, PHONE_RE, SKILL_PATTERNS, extract,
                                   extract_skills)
from tests.conftest import read_sample


def raw(text):
    return [s.text for s in extract_skills(text)]


# TC-E01 — example of the assignment
def test_assignment_example_wednesday():
    r = extract(read_sample("wednesday_addams.txt"))
    assert r.name == "Wednesday Addams"
    assert r.raw_skills == ["JS", "React.js", "NodeJS", "Postgres", "Git"]
    assert r.experience_years == 3
    assert r.experience_summary == "developing web applications"


# TC-E02 — contact information
@pytest.mark.parametrize("text,expected", [
    ("mail: peter.parker@dailybugle.com", "peter.parker@dailybugle.com"),
    ("a.b+cv@uni.edu.co", "a.b+cv@uni.edu.co"),
])
def test_email(text, expected):
    assert EMAIL_RE.findall(text) == [expected]


@pytest.mark.parametrize("text", ["test.example.com", "user@", "@domain.com"])
def test_not_an_email(text):
    assert EMAIL_RE.findall(text) == []


@pytest.mark.parametrize("text", ["+57 300 123 4567", "(602) 555-0199", "+1 212 555 0147"])
def test_phone(text):
    assert PHONE_RE.search(text).group(0).strip() == text


@pytest.mark.parametrize("text", ["(2019 - 2022)", "born in 1998", "3 years"])
def test_not_a_phone(text):
    assert PHONE_RE.search(text) is None


def test_links_and_contact_of_peter_parker():
    r = extract(read_sample("peter_parker.txt"))
    assert r.emails == ["peter.parker@dailybugle.com"]
    assert r.phones == ["+57 300 123 4567"]
    assert r.github == ["github.com/pparker"]
    assert r.linkedin == ["linkedin.com/in/peter-parker"]


# TC-E03 — experience and jobs
def test_jobs_and_education():
    r = extract(read_sample("peter_parker.txt"))
    assert [(j.role, j.company, j.start, j.end) for j in r.jobs] == [
        ("DevOps Engineer", "Oscorp Industries", 2022, "Present"),
        ("Systems Administrator", "Daily Bugle", 2020, "2022"),
    ]
    assert len(r.education) == 1
    ed = r.education[0]
    assert (ed.level, ed.field, ed.institution, ed.year) == (
        "B.Sc.", "Systems Engineering", "Universidad Icesi", 2020)


def test_multiple_degrees():
    r = extract(read_sample("tony_stark.txt"))
    assert [e.level for e in r.education] == ["Ph.D.", "M.Sc."]


def test_experience_abbreviated_years():
    r = extract("Jane Roe\n6 yrs of experience with cloud platforms.")
    assert r.experience_years == 6


# TC-E04 — skills: no normalization at this stage, text is kept as written
def test_skills_are_kept_as_written():
    assert raw("Py Torch, Tensor Flow, sklearn") == ["Py Torch", "Tensor Flow", "sklearn"]


# TC-E05 — custom word boundaries
@pytest.mark.parametrize("text,expected", [
    ("Node.js", ["Node.js"]),                   # not 'js' inside Node.js
    ("Vue.js, React.js", ["Vue.js", "React.js"]),
    ("PostgreSQL and MySQL", ["PostgreSQL", "MySQL"]),  # no 'SQL' inside
    ("GitHub Actions, GitHub", ["GitHub Actions", "GitHub"]),
    ("javascript", ["javascript"]),
])
def test_boundaries(text, expected):
    assert raw(text) == expected


# TC-E06 — leftmost-longest overlap resolution between categories
def test_longest_match_wins():
    mentions = extract_skills("Py Torch")
    assert [(m.category, m.text) for m in mentions] == [("ML_DATA", "Py Torch")]


# TC-E07 — false positives that the patterns avoid
@pytest.mark.parametrize("text", [
    "I rest on weekends and excel at teamwork",
    "the rest of the team",
    "express your ideas",
])
def test_common_words_are_not_skills(text):
    assert raw(text) == []


def test_urls_are_not_scanned_as_skills():
    assert raw("github.com/pparker") == []


# TC-E08 — every variant of the catalog is fully matched by its category regex
# (the case-sensitive ones are tested separately below)
@pytest.mark.parametrize("category,variant", [
    (c, v) for c, entries in LEXICON.items() for vs in entries.values() for v in vs
    if v not in ("r", "shell", "express", "excel", "rest")
])
def test_catalog_variant_is_extracted(category, variant):
    m = SKILL_PATTERNS[category].fullmatch(variant)
    assert m is not None, f"{variant!r} not matched by {category} pattern"


@pytest.mark.parametrize("variant", ["R", "Shell", "Express", "Excel", "REST"])
def test_case_sensitive_variants(variant):
    assert raw(variant) == [variant]