from __future__ import annotations

import shutil
import subprocess
import sys
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from resumelens.catalog import CATEGORIES, LEXICON  # noqa: E402
from resumelens.normalization import build_transducer  # noqa: E402
from resumelens.profiles import PROFILES  # noqa: E402
from resumelens.recognition import LAMBDA, build_automaton  # noqa: E402

DIAGRAMS = ROOT / "docs" / "diagrams"
GENERATED = ROOT / "docs" / "generated"
KIND_NAME = {"DFA": "DFA", "NFA": "NFA", "ENFA": "ε-NFA"}


def show(sym: str) -> str:
    return {" ": "␣"}.get(sym, sym)


def dot_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def render(dot_text: str, stem: str) -> None:
    dot_path = DIAGRAMS / f"{stem}.dot"
    dot_path.write_text(dot_text, encoding="utf-8")
    if shutil.which("dot"):
        subprocess.run(["dot", "-Tsvg", str(dot_path), "-o", str(DIAGRAMS / f"{stem}.svg")],
                       check=True)



# Transducers


def merged_fst_edges(spec):
    """Group case variants: (src, dst, out) -> ['r', 'R']."""
    groups: "OrderedDict[tuple[str, str, str], list[str]]" = OrderedDict()
    for src, sym, dst, out in spec.transitions:
        groups.setdefault((src, dst, out), []).append(sym)
    return groups


def fst_dot(spec) -> str:
    lines = [f'digraph "{spec.name}" {{', "  rankdir=LR;",
             '  node [shape=circle fontname="Helvetica" fontsize=10];',
             '  edge [fontname="Helvetica" fontsize=9];',
             '  start [shape=point];', "  start -> q0;",
             '  qf [shape=doublecircle];']
    for (src, dst, out), syms in merged_fst_edges(spec).items():
        label = "|".join(show(s) for s in syms) + " : " + out
        lines.append(f'  {src} -> {dst} [label="{dot_escape(label)}"];')
    lines.append("}")
    return "\n".join(lines)


def fst_markdown(spec, category: str) -> str:
    md = [f"## {spec.name}", ""]
    md.append("Transformations modelled:")
    md.append("")
    for canonical, variants in LEXICON[category].items():
        md.append(f"- {', '.join(f'`{v}`' for v in variants)} → `{canonical}`")
    md += ["", f"M = (Q, Σ, Γ, δ, ω, q0, F) where", ""]
    md.append(f"- **Q** = {{{', '.join(spec.states)}}}  (|Q| = {len(spec.states)})")
    md.append(f"- **Σ** = {{{', '.join(show(s) for s in spec.input_alphabet)}}}  "
              f"(|Σ| = {len(spec.input_alphabet)}; `␣` is the blank, `#` the end marker)")
    md.append(f"- **Γ** = {{{', '.join(spec.output_alphabet)}}}")
    md.append(f"- **q0** = {spec.start}")
    md.append(f"- **F** = {{{', '.join(spec.finals)}}}")
    md.append("- **δ : Q × Σ → Q** and **ω : Q × Σ → Γ ∪ {λ}** are given by the table "
              "(a row with `a|A` stands for two transitions with the same target and output). "
              "Every pair not listed is undefined (the transducer rejects).")
    md += ["", "| State | Input | δ (next state) | ω (output) |", "|---|---|---|---|"]
    for (src, dst, out), syms in merged_fst_edges(spec).items():
        md.append(f"| {src} | `{'|'.join(show(s) for s in syms)}` | {dst} | {out} |")
    md += ["", f"Diagram: [`{spec.name}.svg`](../diagrams/{spec.name}.svg)", ""]
    return "\n".join(md)


# Automata


def automaton_dot(spec) -> str:
    finals = set(spec.finals)
    lines = [f'digraph "{spec.profile}_{spec.kind}" {{', "  rankdir=LR;",
             '  node [shape=circle fontname="Helvetica" fontsize=11];',
             '  edge [fontname="Helvetica" fontsize=9];',
             "  start [shape=point];", f"  start -> {spec.start};"]
    for s in spec.states:
        if s in finals:
            lines.append(f"  {s} [shape=doublecircle];")
    groups: "OrderedDict[tuple[str, str], list[str]]" = OrderedDict()
    for src, sym, dst in spec.transitions:
        groups.setdefault((src, dst), []).append(sym)
    for (src, dst), syms in groups.items():
        style = ' style=dashed' if syms == [LAMBDA] else ""
        lines.append(f'  {src} -> {dst} [label="{dot_escape(chr(10).join(syms))}"{style}];')
    lines.append("}")
    return "\n".join(lines)


def justification(spec) -> str:
    delta = spec.delta()
    if spec.kind == "DFA":
        return ("It is a **DFA**: there are no λ-transitions and for every pair (q, a) "
                "δ(q, a) contains at most one state (the alternative sets of different "
                "slots are disjoint). δ is a *partial* function Q × Σ → Q; the missing "
                "pairs go to an implicit dead state, which is why pyformlang's "
                "`is_deterministic()` returns True.")
    multi = next(((q, a, d) for (q, a), d in delta.items() if len(d) > 1), None)
    example = (f" For example δ({multi[0]}, {multi[1]}) = {{{', '.join(multi[2])}}}."
               if multi else "")
    if spec.kind == "NFA":
        return ("It is an **NFA** (without λ-transitions): δ : Q × Σ → ℘(Q) and some pairs "
                "have more than one successor, because on reading a symbol of a slot the "
                "automaton guesses whether it is the last one of that slot." + example)
    lam = [(q, d) for (q, a), d in delta.items() if a == LAMBDA]
    return ("It is an **ε-NFA (λ-NFA)**: δ : Q × (Σ ∪ {λ}) → ℘(Q) and it contains "
            f"{sum(len(d) for _, d in lam)} λ-transitions, used to repeat a slot "
            "(t → s), to move to the next slot and to skip optional slots." + example)


def pattern_text(profile) -> str:
    parts = []
    for s in profile.slots:
        alt = "(" + " | ".join(s.alternatives) + ")"
        parts.append(alt + ("*" if s.optional else "⁺"))
    return " · ".join(parts)


def automaton_markdown(profile, spec) -> str:
    delta = spec.delta()
    md = [f"## {profile.title} — {KIND_NAME[spec.kind]}", ""]
    md.append(f"**Profile pattern.** {profile.summary}")
    md += ["", "Slots in canonical order:", ""]
    for i, s in enumerate(profile.slots, 1):
        md.append(f"{i}. `{s.name}`{' (optional)' if s.optional else ''}: "
                  f"{' | '.join(s.alternatives)}")
    md += ["", f"Recognised language (regular expression over tokens): "
               f"L = {pattern_text(profile)}", ""]
    md.append(f"M = (Q, Σ, δ, q0, F) where")
    md.append("")
    md.append(f"- **Q** = {{{', '.join(spec.states)}}}")
    md.append(f"- **Σ** = {{{', '.join(spec.alphabet)}}}")
    md.append(f"- **q0** = {spec.start}")
    md.append(f"- **F** = {{{', '.join(spec.finals)}}}")
    md.append("- **δ** (pairs not listed are undefined / ∅):")
    md += ["", "| State | Symbol | δ |", "|---|---|---|"]
    for (q, a), dst in delta.items():
        value = dst[0] if spec.kind == "DFA" else "{" + ", ".join(dst) + "}"
        md.append(f"| {q} | {a} | {value} |")
    md += ["", f"**Type.** {justification(spec)}", "",
           f"Diagram: [`{profile.key}_{spec.kind}.svg`](../diagrams/{profile.key}_{spec.kind}.svg)",
           ""]
    return "\n".join(md)


def main() -> None:
    DIAGRAMS.mkdir(parents=True, exist_ok=True)
    GENERATED.mkdir(parents=True, exist_ok=True)

    fst_parts = ["# Generated — Finite-state transducers (Stage 2)", "",
                 "> Generated by `tools/generate_docs.py` from `resumelens/catalog.py`. "
                 "Do not edit by hand.", ""]
    for category in CATEGORIES:
        spec = build_transducer(category)
        render(fst_dot(spec), spec.name)
        fst_parts.append(fst_markdown(spec, category))
    (GENERATED / "transducers.md").write_text("\n".join(fst_parts), encoding="utf-8")

    fa_parts = ["# Generated — Finite automata (Stage 3)", "",
                "> Generated by `tools/generate_docs.py` from `resumelens/profiles.py`. "
                "Do not edit by hand.", ""]
    for profile in PROFILES.values():
        spec = build_automaton(profile)
        render(automaton_dot(spec), f"{profile.key}_{spec.kind}")
        fa_parts.append(automaton_markdown(profile, spec))
    (GENERATED / "automata.md").write_text("\n".join(fa_parts), encoding="utf-8")

    # Small illustrative transducer for the docs / poster (JS family only).
    from resumelens import catalog
    saved = catalog.LEXICON["LANGUAGES"]
    catalog.LEXICON["LANGUAGES"] = {"JAVASCRIPT": ("js", "javascript")}
    try:
        mini = build_transducer("LANGUAGES")
        mini.name = "T_EXAMPLE_JAVASCRIPT"
        render(fst_dot(mini), mini.name)
    finally:
        catalog.LEXICON["LANGUAGES"] = saved
    print("Generated docs/generated/*.md and docs/diagrams/*")


if __name__ == "__main__":
    main()
