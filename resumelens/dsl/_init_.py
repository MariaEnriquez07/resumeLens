"""Stage 4 — Candidate Profile Language (RCPL) with textX.

* ``metamodel()``           builds the textX metamodel from ``resume.tx``;
* ``parse(text)``           parses and validates a profile specification;
* ``to_dsl(...)``           serialises the results of Stages 1–3 as RCPL text.

Validation has two layers:

1. **Lexical / syntactic** – done by the textX parser generated from the
   grammar. Any violation raises ``textx.exceptions.TextXSyntaxError``.
2. **Semantic** – object processors registered on the metamodel. Violations
   raise ``textx.exceptions.TextXSemanticError``. They check context-sensitive
   rules that a context-free grammar cannot express:
     * a skill belongs to the category of its group and is not repeated;
     * each profile is classified once, and an ACCEPTED profile lists its
       sequence and has no missing requirements.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from textx import get_location, metamodel_from_file
from textx.exceptions import TextXSemanticError, TextXSyntaxError

from ..catalog import CATEGORIES, token_category
from ..extraction import ExtractionResult
from ..normalization import NormalizationResult
from ..recognition import ProfileResult

GRAMMAR_FILE = Path(__file__).with_name("resume.tx")

__all__ = [
    "GRAMMAR_FILE", "metamodel", "parse", "parse_file", "to_dsl",
    "TextXSemanticError", "TextXSyntaxError",
]


# --------------------------------------------------------------------------- #
# Semantic rules (object processors)
# --------------------------------------------------------------------------- #

def _err(msg: str, obj) -> TextXSemanticError:
    return TextXSemanticError(msg, **get_location(obj))


def _check_skill_group(group) -> None:
    seen = set()
    for skill in group.skills:
        category = token_category(skill)
        if category is None:
            raise _err(f"Unknown skill '{skill}'", group)
        if category != group.category:
            raise _err(f"Skill '{skill}' belongs to {category}, not {group.category}", group)
        if skill in seen:
            raise _err(f"Duplicated skill '{skill}' in {group.category}", group)
        seen.add(skill)


def _check_classification(section) -> None:
    names = [r.profile for r in section.results]
    if len(names) != len(set(names)):
        raise _err("A profile is classified more than once", section)
    for r in section.results:
        if r.status == "ACCEPTED" and not r.sequence:
            raise _err(f"Accepted profile {r.profile} must list its sequence", r)
        if r.status == "ACCEPTED" and r.missing:
            raise _err(f"Accepted profile {r.profile} cannot have missing requirements", r)


@lru_cache(maxsize=1)
def metamodel():
    mm = metamodel_from_file(str(GRAMMAR_FILE))
    mm.register_obj_processors({
        "SkillGroup": _check_skill_group,
        "ClassificationSection": _check_classification,
    })
    return mm


def parse(text: str):
    """Parse + validate RCPL text. Raises TextXSyntaxError / TextXSemanticError."""
    return metamodel().model_from_str(text)


def parse_file(path: str | Path):
    return metamodel().model_from_file(str(path))


# --------------------------------------------------------------------------- #
# Serialiser: pipeline results -> RCPL text
# --------------------------------------------------------------------------- #

_LEVELS = [
    ("ph", "PHD"), ("doctor", "PHD"),
    ("m", "MASTER"),
    ("b", "BACHELOR"),
    ("technologist", "TECHNOLOGIST"),
    ("technician", "TECHNICIAN"),
]


def _degree_level(raw: str) -> str:
    low = raw.lower().replace(".", "").replace(" ", "")
    for prefix, level in _LEVELS:
        if low.startswith(prefix):
            return level
    return "BACHELOR"


def _q(value: str) -> str:
    return '"' + value.replace("\\", "/").replace('"', "'") + '"'


def to_dsl(extraction: ExtractionResult, normalization: NormalizationResult,
           results: list[ProfileResult]) -> str:
    lines = ["resume {", f"    candidate {_q(extraction.name or 'Unknown candidate')};", ""]

    lines.append("    contact {")
    for e in extraction.emails:
        lines.append(f"        email: {e};")
    for p in extraction.phones:
        lines.append(f"        phone: {p};")
    for url in extraction.linkedin:
        lines.append(f"        linkedin: {url if url.startswith('http') else 'https://' + url};")
    for url in extraction.github:
        lines.append(f"        github: {url if url.startswith('http') else 'https://' + url};")
    lines.append("    }")

    if extraction.education:
        lines += ["", "    education {"]
        for ed in extraction.education:
            parts = [f"degree {_degree_level(ed.level)} {_q(ed.field)}"]
            if ed.institution:
                parts.append(f"at {_q(ed.institution)}")
            if ed.year:
                parts.append(f"year {ed.year}")
            lines.append("        " + " ".join(parts) + ";")
        lines.append("    }")

    if extraction.experience_years is not None or extraction.jobs:
        lines += ["", "    experience {"]
        if extraction.experience_years is not None:
            lines.append(f"        total years: {extraction.experience_years};")
        if extraction.experience_summary:
            lines.append(f"        summary: {_q(extraction.experience_summary)};")
        for job in extraction.jobs:
            end = job.end if job.end.isdigit() else "PRESENT"
            lines.append(f"        job {_q(job.role)} at {_q(job.company)} "
                         f"from {job.start} to {end};")
        lines.append("    }")

    lines += ["", "    skills {"]
    groups = normalization.by_category()
    for category in CATEGORIES:
        if category in groups:
            lines.append(f"        {category}: {', '.join(groups[category])};")
    lines.append("    }")

    lines += ["", "    classification {"]
    for r in results:
        line = f"        profile {r.profile} is {r.status} via {r.automaton_kind}"
        if r.sequence:
            line += f"\n            sequence: {', '.join(r.sequence)}"
        if r.missing:
            line += "\n            missing: " + ", ".join(_q(m) for m in r.missing)
        lines.append(line + ";")
    lines += ["    }", "}", ""]
    return "\n".join(lines)