"""Glue code: runs the four stages in order.

    text ──Stage1──▶ ExtractionResult ──Stage2──▶ NormalizationResult
         ──Stage3──▶ [ProfileResult] ──Stage4──▶ RCPL text ─parse─▶ model ─▶ HTML
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from . import dsl
from .extraction import ExtractionResult, extract
from .normalization import NormalizationResult, Normalizer
from .recognition import ProfileResult, Recognizer
from .render import to_html


@dataclass
class AnalysisResult:
    extraction: ExtractionResult
    normalization: NormalizationResult
    classification: list[ProfileResult]
    dsl_text: str
    model: object
    html: str

    @property
    def accepted_profiles(self) -> list[str]:
        return [r.profile for r in self.classification if r.accepted]

    def save(self, out_dir: str | Path, stem: str = "candidate") -> dict[str, Path]:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        paths = {
            "extraction": out / f"{stem}.extraction.json",
            "normalization": out / f"{stem}.normalization.json",
            "classification": out / f"{stem}.classification.json",
            "dsl": out / f"{stem}.resume",
            "html": out / f"{stem}.html",
        }
        self.extraction.save_json(paths["extraction"])
        paths["normalization"].write_text(json.dumps(asdict(self.normalization), indent=2),
                                          encoding="utf-8")
        paths["classification"].write_text(
            json.dumps([asdict(r) | {"status": r.status} for r in self.classification],
                       indent=2), encoding="utf-8")
        paths["dsl"].write_text(self.dsl_text, encoding="utf-8")
        paths["html"].write_text(self.html, encoding="utf-8")
        return paths


class ResumeLens:
    """One general solution for every profile (profiles are data, not code)."""

    def __init__(self) -> None:
        self.normalizer = Normalizer()
        self.recognizer = Recognizer()

    def analyze(self, text: str) -> AnalysisResult:
        extraction = extract(text)                                            # Stage 1
        normalization = self.normalizer.normalize(
            [(s.text, s.category) for s in extraction.skills])                # Stage 2
        classification = self.recognizer.classify(normalization.tokens)       # Stage 3
        dsl_text = dsl.to_dsl(extraction, normalization, classification)      # Stage 4
        model = dsl.parse(dsl_text)          # validation: raises if the spec is invalid
        return AnalysisResult(extraction, normalization, classification, dsl_text,
                              model, to_html(model))
