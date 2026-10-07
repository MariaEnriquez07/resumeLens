"""Stage 2 — Qualification normalization with finite-state transducers.

One deterministic finite-state transducer (FST) is built per category of the
catalog. Each transducer

    M = (Q, Σ, Γ, δ, ω, q0, F)

reads a raw skill string **character by character**, followed by the end
marker ``#``, and writes its canonical token:

* Q  = one state per distinct prefix of the variants (a trie) plus the final
       state ``qf``;
* Σ  = the characters used in the variants (both cases of each letter) ∪ {#};
* Γ  = the canonical tokens of the category (e.g. JAVASCRIPT, REACT);
* δ  = trie transitions; for each letter both the lower- and upper-case form
       lead to the same state (the transducer models case-insensitivity);
* ω  = λ (empty output) on every character transition and the canonical
       token on the ``#`` transition that closes a complete variant;
* q0 = the state of the empty prefix;
* F  = {qf}.

The end marker is needed because some variants are prefixes of others
("react" / "react.js"): the output can only be decided when the whole input
has been read.

Example (LANGUAGES transducer):  J S #  ↦  JAVASCRIPT
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from pyformlang.fst import FST

from .catalog import CATEGORIES, LEXICON, global_order_key, token_category
from .profiles import Profile

END = "#"
LAMBDA: list[str] = []  # empty output


@dataclass
class TransducerSpec:
    """Explicit components of one transducer (used for docs and diagrams)."""
    name: str
    states: list[str]
    input_alphabet: list[str]
    output_alphabet: list[str]
    # (from, input symbol, to, output symbol or "λ")
    transitions: list[tuple[str, str, str, str]]
    start: str
    finals: list[str]
    fst: FST = field(repr=False, default=None)  # type: ignore[assignment]


def _case_variants(ch: str) -> list[str]:
    variants = {ch, ch.lower(), ch.upper()}
    return sorted(v for v in variants if len(v) == 1)


def build_transducer(category: str) -> TransducerSpec:
    """Build the trie-shaped FST for one category of the catalog."""
    entries = LEXICON[category]
    prefix_state: dict[str, str] = {"": "q0"}
    transitions: list[tuple[str, str, str, str]] = []
    input_alphabet: set[str] = {END}

    def state_for(prefix: str) -> str:
        if prefix not in prefix_state:
            prefix_state[prefix] = f"q{len(prefix_state)}"
        return prefix_state[prefix]

    for canonical, variants in entries.items():
        for variant in variants:
            for i, ch in enumerate(variant):
                src = state_for(variant[:i])
                dst_prefix = variant[: i + 1]
                is_new = dst_prefix not in prefix_state
                dst = state_for(dst_prefix)
                if is_new:
                    for c in _case_variants(ch):
                        transitions.append((src, c, dst, "λ"))
                        input_alphabet.add(c)
            last = state_for(variant)
            transitions.append((last, END, "qf", canonical))

    fst = FST()
    for src, sym, dst, out in transitions:
        fst.add_transition(src, sym, dst, [] if out == "λ" else [out])
    fst.add_start_state("q0")
    fst.add_final_state("qf")

    states = list(prefix_state.values()) + ["qf"]
    return TransducerSpec(
        name=f"T_{category}",
        states=states,
        input_alphabet=sorted(input_alphabet),
        output_alphabet=list(entries.keys()),
        transitions=transitions,
        start="q0",
        finals=["qf"],
        fst=fst,
    )


_WS = re.compile(r"\s+")


def preprocess(raw: str) -> str:
    """Collapse internal whitespace and trim trailing punctuation.

    This is the only transformation applied outside the transducers; it
    guarantees that the input is a word over Σ (single spaces only)."""
    return _WS.sub(" ", raw).strip().strip(".,;:")


@dataclass
class NormalizationResult:
    tokens: list[str]                       # canonical tokens, global order
    mapping: list[tuple[str, str, str]]     # (raw, canonical, transducer)
    unrecognized: list[str]

    def by_category(self) -> dict[str, list[str]]:
        groups: dict[str, list[str]] = {c: [] for c in CATEGORIES}
        for tok in self.tokens:
            groups[token_category(tok) or "TOOLS"].append(tok)
        return {c: toks for c, toks in groups.items() if toks}


class Normalizer:
    """Runs every category transducer over each extracted string."""

    def __init__(self) -> None:
        self.transducers: dict[str, TransducerSpec] = {
            c: build_transducer(c) for c in CATEGORIES
        }

    def translate(self, raw: str, category: str | None = None) -> tuple[str, str] | None:
        """Return (canonical token, transducer name) or None.

        If ``category`` (from Stage 1) is given, that transducer is tried
        first; the others are a fallback."""
        word = list(preprocess(raw)) + [END]
        order = list(CATEGORIES)
        if category in order:
            order.remove(category)
            order.insert(0, category)
        for cat in order:
            spec = self.transducers[cat]
            outputs = list(spec.fst.translate(word))
            if outputs:
                return outputs[0][0], spec.name
        return None

    def normalize(self, raw_items: list[str] | list[tuple[str, str]]) -> NormalizationResult:
        tokens: list[str] = []
        mapping: list[tuple[str, str, str]] = []
        unknown: list[str] = []
        for item in raw_items:
            raw, cat = (item, None) if isinstance(item, str) else item
            result = self.translate(raw, cat)
            if result is None:
                unknown.append(raw)
                continue
            token, name = result
            mapping.append((raw, token, name))
            if token not in tokens:
                tokens.append(token)
        tokens.sort(key=global_order_key)
        return NormalizationResult(tokens, mapping, unknown)


def sort_for_profile(tokens: list[str], profile: Profile) -> list[str]:
    """Canonical order defined by the profile (input for Stage 3)."""
    return profile.canonical_sequence(tokens)