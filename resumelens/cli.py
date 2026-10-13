"""Command-line interface.

    python -m resumelens analyze samples/wednesday_addams.txt --out output/
    python -m resumelens analyze samples/ --out output/        (whole folder)
    python -m resumelens validate output/wednesday_addams.resume
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import dsl


def _print_analysis(name: str, result) -> None:
    ex, no = result.extraction, result.normalization
    print(f"\n=== {name} ===")
    print(f"Candidate : {ex.name}")
    print(f"Stage 1   : {', '.join(ex.raw_skills) or '(no skills found)'}")
    print(f"Stage 2   : {', '.join(no.tokens) or '(none)'}")
    if no.unrecognized:
        print(f"            unrecognized: {', '.join(no.unrecognized)}")
    print("Stage 3   :")
    for r in result.classification:
        seq = " ".join(r.sequence) or "ε"
        print(f"   {r.status:<8} {r.profile:<27} [{r.automaton_kind}] {seq}")
        if r.missing:
            print(f"            missing: {', '.join(r.missing)}")
    print("Stage 4   : profile specification validated by the textX grammar")


def cmd_analyze(args) -> int:
    from .pipeline import ResumeLens
    lens = ResumeLens()
    src = Path(args.path)
    files = sorted(src.glob("*.txt")) if src.is_dir() else [src]
    if not files:
        print(f"No .txt résumés found in {src}", file=sys.stderr)
        return 1
    for f in files:
        result = lens.analyze(f.read_text(encoding="utf-8"))
        _print_analysis(f.name, result)
        if args.out:
            paths = result.save(args.out, f.stem)
            print(f"            written: {paths['dsl']}  {paths['html']}")
    return 0


def cmd_validate(args) -> int:
    try:
        model = dsl.parse_file(args.path)
    except dsl.TextXSyntaxError as e:
        print(f"REJECTED (syntax error) {e.line}:{e.col}: {e.message}")
        return 2
    except dsl.TextXSemanticError as e:
        print(f"REJECTED (semantic error) {e.line}:{e.col}: {e.message}")
        return 3
    print(f"VALID candidate profile: {model.candidate.name}")
    if args.html:
        from .render import to_html
        Path(args.html).write_text(to_html(model), encoding="utf-8")
        print(f"HTML written to {args.html}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="resumelens",
                                     description="Formal-language-based résumé screening")
    sub = parser.add_subparsers(dest="command", required=True)

    a = sub.add_parser("analyze", help="run the full pipeline on a résumé or folder")
    a.add_argument("path")
    a.add_argument("--out", help="folder for JSON, .resume and HTML outputs")
    a.set_defaults(func=cmd_analyze)

    v = sub.add_parser("validate", help="validate a .resume specification")
    v.add_argument("path")
    v.add_argument("--html", help="write the HTML visualization to this file")
    v.set_defaults(func=cmd_validate)

    args = parser.parse_args(argv)
    return args.func(args)
