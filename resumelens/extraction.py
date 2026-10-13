"""Stage 1 — Résumé information extraction with regular expressions.

This stage only *finds* strings in the raw text and keeps them exactly as they
are written ("Py Torch" stays "Py Torch"). Deciding that two strings mean the
same thing is the job of Stage 2.

Every regular expression is explained in ``docs/stage1_regex.md``.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

# --------------------------------------------------------------------------- #
# 1. Contact information
# --------------------------------------------------------------------------- #

# user @ domain . tld        e.g. peter.parker@dailybugle.com
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")

# [+country ] area number    e.g. +57 300 123 4567  |  (602) 555-0199
PHONE_RE = re.compile(r"(?:\+\d{1,3} )?(?:\(\d{3}\)|\d{3})[ -]\d{3}[ -]\d{4}")

# linkedin.com/in/<user>   and   github.com/<user>
LINKEDIN_RE = re.compile(r"linkedin\.com/in/[\w-]+", re.IGNORECASE)
GITHUB_RE = re.compile(r"github\.com/[\w-]+", re.IGNORECASE)

# The first line of the résumé: 2 to 4 capitalised words  e.g. Mary Jane Watson
NAME_RE = re.compile(r"^([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?: [A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,3})$")

# --------------------------------------------------------------------------- #
# 2. Professional experience
# --------------------------------------------------------------------------- #

# "3 years of experience developing web applications."
EXPERIENCE_RE = re.compile(r"(\d+)\+? (?:years?|yrs?) of experience ?([^.\n]*)",
                           re.IGNORECASE)

# "DevOps Engineer at Oscorp Industries (2022 - Present)"
JOB_RE = re.compile(r"^-? ?(.+?) at (.+?) \((\d{4}) - (\d{4}|Present)\)", re.MULTILINE)

# --------------------------------------------------------------------------- #
# 3. Academic qualifications
# --------------------------------------------------------------------------- #

# "B.Sc. in Systems Engineering, Universidad Icesi (2020)"
EDUCATION_RE = re.compile(
    r"^(Ph\.D\.|M\.Sc\.|B\.Sc\.|Master of Science|Bachelor of Science)"
    r" in (.+?), (.+?) \((\d{4})\)$",
    re.MULTILINE,
)

# --------------------------------------------------------------------------- #
# 4. Qualifications: one regular expression per category
# --------------------------------------------------------------------------- #
# Inside each category the longest alternatives are written first, because a
# Python alternation takes the first alternative that matches
# ("node.js" must be tried before "node", "postgresql" before "sql").
# (?-i:...) makes a part case-sensitive: "R", "Shell", "Express", "Excel" and
# "REST" are only skills when written with that capitalisation.

SKILL_PATTERNS_TEXT: dict[str, str] = {
    "ML_DATA": r"scikit[ -]learn|sklearn|tensor ?flow|py ?torch|pandas|numpy"
               r"|machine learning|predictive models",
    "DEVOPS_CLOUD": r"github actions|gitlab[ -]ci|amazon web services|google cloud"
                    r"|kubernetes|k8s|docker|jenkins|linux|ubuntu|aws|azure|gcp"
                    r"|terraform|ansible",
    "FRAMEWORKS": r"react\.js|reactjs|react|angularjs|angular|vue\.js|vue"
                  r"|node\.js|nodejs|node|express\.js|(?-i:Express)|django"
                  r"|spring ?boot|rest apis?|(?-i:REST)",
    "DATABASES": r"postgresql|postgres|mysql|mongodb|mongo|sqlite|no-?sql|sql",
    "LANGUAGES": r"javascript|js|typescript|ts|python|py|bash|(?-i:Shell)|(?-i:R)",
    "TOOLS": r"github|git|ms excel|(?-i:Excel)|power ?bi|tableau|statistics",
}

# Each category on its own (used to document and test it).
SKILL_PATTERNS: dict[str, re.Pattern[str]] = {
    cat: re.compile(rf"\b(?:{text})\b", re.IGNORECASE)
    for cat, text in SKILL_PATTERNS_TEXT.items()
}

# All categories joined with "|". Each one is a named group, so the name of
# the group that matched is the category. The order of the groups matters:
# "Py Torch" must be tried as ML_DATA before "Py" is tried as LANGUAGES, and
# "GitHub Actions" (DEVOPS_CLOUD) before "GitHub" (TOOLS).
SKILL_RE = re.compile(
    r"\b(?:" + "|".join(f"(?P<{cat}>{text})" for cat, text in SKILL_PATTERNS_TEXT.items())
    + r")\b",
    re.IGNORECASE,
)

# --------------------------------------------------------------------------- #
# Result objects
# --------------------------------------------------------------------------- #


@dataclass
class SkillMention:
    category: str
    text: str
    start: int
    end: int


@dataclass
class Job:
    role: str
    company: str
    start: int
    end: str


@dataclass
class Education:
    level: str
    field: str
    institution: str
    year: int


@dataclass
class ExtractionResult:
    name: str | None = None
    emails: list[str] = field(default_factory=list)
    phones: list[str] = field(default_factory=list)
    linkedin: list[str] = field(default_factory=list)
    github: list[str] = field(default_factory=list)
    experience_years: int | None = None
    experience_summary: str | None = None
    jobs: list[Job] = field(default_factory=list)
    education: list[Education] = field(default_factory=list)
    skills: list[SkillMention] = field(default_factory=list)

    @property
    def raw_skills(self) -> list[str]:
        """Skill strings exactly as written (input for Stage 2)."""
        return [s.text for s in self.skills]

    def to_dict(self) -> dict:
        return asdict(self)

    def save_json(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False),
                              encoding="utf-8")


# --------------------------------------------------------------------------- #
# Extraction functions
# --------------------------------------------------------------------------- #


def _unique(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))


def extract_name(text: str) -> str | None:
    first_line = text.strip().splitlines()[0].strip() if text.strip() else ""
    m = NAME_RE.match(first_line)
    return m.group(1) if m else None


def extract_skills(text: str) -> list[SkillMention]:
    """Find every qualification mention, left to right."""
    # E-mails and profile links are removed first, so "github.com/pparker"
    # is not read as the skill "github".
    for pattern in (EMAIL_RE, LINKEDIN_RE, GITHUB_RE):
        text = pattern.sub(lambda m: " " * len(m.group(0)), text)
    return [SkillMention(m.lastgroup, m.group(0), m.start(), m.end())
            for m in SKILL_RE.finditer(text)]


def extract_experience(text: str) -> tuple[int | None, str | None, list[Job]]:
    years = summary = None
    m = EXPERIENCE_RE.search(text)
    if m:
        years = int(m.group(1))
        summary = m.group(2).strip() or None
    jobs = [Job(role, company, int(start), end)
            for role, company, start, end in JOB_RE.findall(text)]
    return years, summary, jobs


def extract_education(text: str) -> list[Education]:
    return [Education(level, field_, institution, int(year))
            for level, field_, institution, year in EDUCATION_RE.findall(text)]


def extract(text: str) -> ExtractionResult:
    """Run every Stage-1 pattern over a résumé."""
    years, summary, jobs = extract_experience(text)
    return ExtractionResult(
        name=extract_name(text),
        emails=_unique(EMAIL_RE.findall(text)),
        phones=_unique(PHONE_RE.findall(text)),
        linkedin=_unique(LINKEDIN_RE.findall(text)),
        github=_unique(GITHUB_RE.findall(text)),
        experience_years=years,
        experience_summary=summary,
        jobs=jobs,
        education=extract_education(text),
        skills=extract_skills(text),
    )
