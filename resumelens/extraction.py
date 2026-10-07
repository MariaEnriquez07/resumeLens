"""Stage 1 — Résumé information extraction with regular expressions.

This stage only *finds* candidate strings in the raw text. It does NOT decide
whether two strings are equivalent (that is Stage 2) nor whether the candidate
fits a profile (that is Stage 3). Every string is reported exactly as written.

Each pattern is documented in ``docs/stage1_regex.md``.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path

# --------------------------------------------------------------------------- #
# Contact information
# --------------------------------------------------------------------------- #

# local-part @ domain . tld  (one or more dot-separated labels after the @)
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+")

# optional +country code, optional (area), then groups of digits separated by
# spaces or hyphens. The look-arounds prevent matching inside longer numbers.
PHONE_RE = re.compile(
    r"(?<![\w+])"
    r"(?:\+\d{1,3}[\s-]?)?"
    r"(?:\(\d{1,4}\)[\s-]?)?"
    r"\d{3}[\s-]?\d{3,4}(?:[\s-]?\d{2,4})?"
    r"(?![\w])"
)

LINKEDIN_RE = re.compile(r"(?:https?://)?(?:www\.)?linkedin\.com/in/[A-Za-z0-9_-]+/?",
                         re.IGNORECASE)
GITHUB_RE = re.compile(r"(?:https?://)?(?:www\.)?github\.com/[A-Za-z0-9_-]+/?",
                       re.IGNORECASE)

# Candidate name: the first non-empty line made of 2–4 capitalised words.
_NAME_WORD = r"[A-ZÁÉÍÓÚÑÜ][A-Za-zÁÉÍÓÚÑÜáéíóúñü'’-]+"
NAME_RE = re.compile(rf"^[ \t]*({_NAME_WORD}(?:[ \t]+{_NAME_WORD}){{1,3}})[ \t]*$")

# --------------------------------------------------------------------------- #
# Professional experience
# --------------------------------------------------------------------------- #

# "3 years of experience developing web applications."
EXPERIENCE_SUMMARY_RE = re.compile(
    r"(?P<years>\d{1,2})\+?\s*(?:years?|yrs?)\s+of\s+(?:professional\s+)?experience"
    r"(?:\s+(?P<field>(?:in|as|developing|building|with|on|designing|working)\s+[^.\n]+))?",
    re.IGNORECASE,
)

# "Software Engineer at Acme Corp (2019 - 2022)"  /  "... (2021 - Present)"
JOB_RE = re.compile(
    r"^[ \t]*[-*•]?[ \t]*"
    r"(?P<role>[A-Z][A-Za-z/&+ -]{2,60}?)\s+at\s+"
    r"(?P<company>[A-Z][A-Za-z0-9&.' -]{1,60}?)\s*"
    r"\(\s*(?P<start>(?:19|20)\d{2})\s*[-–]\s*"
    r"(?P<end>(?:19|20)\d{2}|[Pp]resent|[Aa]ctualidad)\s*\)",
    re.MULTILINE,
)

# --------------------------------------------------------------------------- #
# Academic qualifications
# --------------------------------------------------------------------------- #

# "B.Sc. in Systems Engineering, Universidad Icesi (2022)"
EDUCATION_RE = re.compile(
    r"(?P<level>Ph\.?\s?D\.?|Doctorate|M\.?\s?Sc\.?|Master(?:'s)?(?:\s+of\s+Science)?|"
    r"B\.?\s?Sc\.?|B\.?\s?S\.?|Bachelor(?:'s)?(?:\s+of\s+Science)?|Technologist|Technician)"
    r"(?:\s+degree)?\s+(?:in|of)\s+"
    r"(?P<field>[A-Z][A-Za-zÁÉÍÓÚáéíóúñ &-]+?)"
    r"(?:\s*(?:,|\s-\s|\s+at\s+)\s*(?P<institution>[A-Z][A-Za-zÁÉÍÓÚáéíóúñ .&-]+?))?"
    r"\s*(?:\(\s*(?P<year>(?:19|20)\d{2})\s*\))?[ \t]*$",
    re.MULTILINE,
)

# --------------------------------------------------------------------------- #
# Qualifications (skills). One regular expression per category.
# --------------------------------------------------------------------------- #
# A match must not be glued to other word characters. ``(?<![...])`` and
# ``(?![...])`` implement a custom word boundary that also treats '.', '/',
# '#', '+', '@' and '-' as part of a word, so "js" is not found inside
# "Node.js" and "linux" is not found inside "gnu/linux".
_LEFT = r"(?<![\w.#+/@&-])"
_RIGHT = r"(?![\w#+/@&-]|\.\w)"

SKILL_FRAGMENTS: dict[str, list[str]] = {
    "LANGUAGES": [
        r"java\s?script", r"ecmascript", r"js",
        r"type\s?script", r"ts",
        r"python\s?3?", r"py",
        r"java",
        r"bash", r"shell\s+scripting", r"(?-i:Shell)",
        r"(?-i:R)\s?studio", r"(?-i:R)",
    ],
    "FRAMEWORKS": [
        r"react(?:\.js|\s?js)?",
        r"angular(?:\.js|js)?",
        r"vue(?:\.js|js)?",
        r"node(?:\.js|\s?js)?",
        r"express(?:\.js|js)", r"(?-i:Express)",
        r"django",
        r"spring[\s-]?boot",
        r"rest(?:ful)?\s?apis?", r"(?-i:RESTful|REST)", r"api\s+rest",
    ],
    "DATABASES": [
        r"no[\s-]?sql",
        r"postgre\s?sql", r"postgres", r"psql",
        r"my\s?sql",
        r"mongo\s?db", r"mongo",
        r"sqlite",
        r"sql",
    ],
    "ML_DATA": [
        r"pandas",
        r"num\s?py",
        r"scikit[\s-]?learn", r"sklearn",
        r"tensor\s?flow",
        r"py\s?torch", r"torch",
        r"machine[\s-]learning(?:\s+models?)?",
        r"predictive\s+model(?:s|ing)",
        r"ml\s+models?",
        r"model\s+development",
    ],
    "DEVOPS_CLOUD": [
        r"gnu/linux", r"linux", r"ubuntu", r"debian", r"centos",
        r"docker(?:[\s-]compose)?",
        r"kubernetes", r"k8s",
        r"jenkins",
        r"github\s+actions", r"gh\s+actions",
        r"gitlab[\s-]ci(?:/cd)?",
        r"amazon\s+web\s+services", r"aws",
        r"microsoft\s+azure", r"azure",
        r"google\s+cloud(?:\s+platform)?", r"gcp",
        r"terraform", r"ansible",
    ],
    "TOOLS": [
        r"git(?:hub)?",
        r"(?:ms|microsoft)\s+excel", r"(?-i:Excel)",
        r"power[\s-]?bi",
        r"tableau",
        r"statistical\s+analysis", r"statistics", r"estad[ií]stica",
    ],
}

SKILL_PATTERNS: dict[str, re.Pattern[str]] = {
    category: re.compile(_LEFT + "(?:" + "|".join(frags) + ")" + _RIGHT, re.IGNORECASE)
    for category, frags in SKILL_FRAGMENTS.items()
}

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
    years: int


@dataclass
class Education:
    level: str
    field: str
    institution: str | None
    year: int | None


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
    for line in text.splitlines():
        if line.strip():
            m = NAME_RE.match(line)
            return m.group(1) if m else None
    return None


def _mask(text: str, patterns: list[re.Pattern[str]]) -> str:
    """Replace matches with spaces (keeps offsets) so URLs/e-mails are not
    scanned again as skills (e.g. 'github' inside 'github.com/...')."""
    chars = list(text)
    for pat in patterns:
        for m in pat.finditer(text):
            for i in range(m.start(), m.end()):
                chars[i] = " "
    return "".join(chars)


def extract_skills(text: str) -> list[SkillMention]:
    """Find every qualification mention.

    All category patterns are applied; when two matches overlap the longest
    one is kept (leftmost-longest policy), e.g. "Py Torch" (ML_DATA) wins over
    "Py" (LANGUAGES) and "GitHub Actions" wins over "GitHub".
    """
    masked = _mask(text, [EMAIL_RE, LINKEDIN_RE, GITHUB_RE])
    found: list[SkillMention] = []
    for category, pattern in SKILL_PATTERNS.items():
        for m in pattern.finditer(masked):
            found.append(SkillMention(category, m.group(0), m.start(), m.end()))

    found.sort(key=lambda s: (-(s.end - s.start), s.start))
    kept: list[SkillMention] = []
    for s in found:
        if all(s.end <= k.start or s.start >= k.end for k in kept):
            kept.append(s)
    kept.sort(key=lambda s: s.start)
    return kept


def extract_experience(text: str) -> tuple[int | None, str | None, list[Job]]:
    years = summary = None
    m = EXPERIENCE_SUMMARY_RE.search(text)
    if m:
        years = int(m.group("years"))
        summary = m.group("field").strip() if m.group("field") else None

    jobs = []
    for jm in JOB_RE.finditer(text):
        start = int(jm.group("start"))
        end_raw = jm.group("end")
        end_year = int(end_raw) if end_raw.isdigit() else date.today().year
        jobs.append(Job(jm.group("role").strip(), jm.group("company").strip(),
                        start, end_raw, max(0, end_year - start)))
    if years is None and jobs:
        years = sum(j.years for j in jobs)
    return years, summary, jobs


def extract_education(text: str) -> list[Education]:
    out = []
    for m in EDUCATION_RE.finditer(text):
        inst = m.group("institution")
        out.append(Education(
            level=m.group("level"),
            field=m.group("field").strip(),
            institution=inst.strip() if inst else None,
            year=int(m.group("year")) if m.group("year") else None,
        ))
    return out


def extract(text: str) -> ExtractionResult:
    """Run every Stage-1 pattern over a résumé."""
    years, summary, jobs = extract_experience(text)
    return ExtractionResult(
        name=extract_name(text),
        emails=_unique(EMAIL_RE.findall(text)),
        phones=_unique([p.strip() for p in PHONE_RE.findall(text)]),
        linkedin=_unique(LINKEDIN_RE.findall(text)),
        github=_unique(GITHUB_RE.findall(text)),
        experience_years=years,
        experience_summary=summary,
        jobs=jobs,
        education=extract_education(text),
        skills=extract_skills(text),
    )