"""Stage 3 — Qualification-pattern recognition with finite automata.

For a profile with slots S1..Sn (alternatives A1..An) the recognised language
is  L = X1 ... Xn  with  Xi = Ai+  (required)  or  Xi = Ai*  (optional).

Each profile declares the type of automaton that models it
(``Profile.construction``). The three types seen in the course are used:

DFA   (Full Stack Developer, Data Analyst) — ``build_dfa``
    States q0..qn. qi means "slots 1..i are satisfied and the last symbol read
    belongs to slot i". δ(qi, a) = qi for a ∈ Ai (repetition) and
    δ(qi, a) = qj for a ∈ Aj when every slot between i and j is optional.
    The alternative sets of different slots are disjoint, so every
    (state, symbol) pair has at most one successor.

NFA   (Machine Learning Engineer) — ``build_nfa``
    States q0..qn plus pj ("inside slot j, more symbols follow"). On reading
    a ∈ Aj the automaton guesses whether a is the last symbol of the slot:
    δ(qi, a) = {qj, pj} and δ(pj, a) = {pj, qj}.

ε-NFA (DevOps Engineer) — ``build_enfa``
    States s_j (entering slot j) and t_j (slot j done), renamed q0..q(2n-1).
    s_j --a--> t_j for a ∈ Aj,  t_j --λ--> s_j (repeat),
    t_j --λ--> s_{j+1} (next slot),  s_j --λ--> t_j if the slot is optional.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from pyformlang.finite_automaton import (
    DeterministicFiniteAutomaton,
    EpsilonNFA,
    NondeterministicFiniteAutomaton,
    State,
    Symbol,
)
from pyformlang.finite_automaton import Epsilon

from .profiles import PROFILES, Profile, Slot

LAMBDA = "λ"


@dataclass
class AutomatonSpec:
    """Explicit 5-tuple of an automaton (used for docs, diagrams and pyformlang)."""
    profile: str
    kind: str                      # DFA | NFA | ENFA
    states: list[str]
    alphabet: list[str]
    transitions: list[tuple[str, str, str]]   # (from, symbol or λ, to)
    start: str
    finals: list[str]
    automaton: object = field(default=None, repr=False)

    def delta(self) -> dict[tuple[str, str], list[str]]:
        table: dict[tuple[str, str], list[str]] = {}
        for src, sym, dst in self.transitions:
            table.setdefault((src, sym), []).append(dst)
        return table


def _next_slots(slots: tuple[Slot, ...], i: int) -> list[int]:
    """Slots reachable after state i (0-based slot indices), skipping optionals."""
    out = []
    for j in range(i, len(slots)):
        out.append(j)
        if not slots[j].optional:
            break
    return out


def _tail_optional(slots: tuple[Slot, ...], i: int) -> bool:
    """True if every slot after position i (exclusive) is optional."""
    return all(s.optional for s in slots[i:])


def _build(kind: str, profile: Profile, states, transitions, start, finals) -> AutomatonSpec:
    if kind == "DFA":
        fa = DeterministicFiniteAutomaton()
    elif kind == "NFA":
        fa = NondeterministicFiniteAutomaton()
    else:
        fa = EpsilonNFA()
    for src, sym, dst in transitions:
        symbol = Epsilon() if sym == LAMBDA else Symbol(sym)
        fa.add_transition(State(src), symbol, State(dst))
    fa.add_start_state(State(start))
    for f in finals:
        fa.add_final_state(State(f))
    return AutomatonSpec(profile.key, kind, states, profile.alphabet,
                         transitions, start, finals, fa)


def build_dfa(profile: Profile) -> AutomatonSpec:
    slots = profile.slots
    n = len(slots)
    states = [f"q{i}" for i in range(n + 1)]
    transitions: list[tuple[str, str, str]] = []
    for i in range(n + 1):
        if i >= 1:  # repetition inside slot i
            for a in slots[i - 1].alternatives:
                transitions.append((f"q{i}", a, f"q{i}"))
        for j in _next_slots(slots, i):
            for a in slots[j].alternatives:
                transitions.append((f"q{i}", a, f"q{j + 1}"))
    finals = [f"q{i}" for i in range(1, n + 1) if _tail_optional(slots, i)]
    return _build("DFA", profile, states, transitions, "q0", finals)


def build_nfa(profile: Profile) -> AutomatonSpec:
    slots = profile.slots
    n = len(slots)
    states = [f"q{i}" for i in range(n + 1)] + [f"p{j}" for j in range(1, n + 1)]
    transitions: list[tuple[str, str, str]] = []
    for i in range(n + 1):
        for j in _next_slots(slots, i):
            for a in slots[j].alternatives:
                transitions.append((f"q{i}", a, f"q{j + 1}"))   # last of slot
                transitions.append((f"q{i}", a, f"p{j + 1}"))   # more to come
    for j in range(1, n + 1):
        for a in slots[j - 1].alternatives:
            transitions.append((f"p{j}", a, f"p{j}"))
            transitions.append((f"p{j}", a, f"q{j}"))
    finals = [f"q{i}" for i in range(1, n + 1) if _tail_optional(slots, i)]
    return _build("NFA", profile, states, transitions, "q0", finals)


def build_enfa(profile: Profile) -> AutomatonSpec:
    slots = profile.slots
    n = len(slots)

    def s(j: int) -> str:  # entering slot j (0-based)
        return f"q{2 * j}"

    def t(j: int) -> str:  # slot j satisfied
        return f"q{2 * j + 1}"

    states = [f"q{k}" for k in range(2 * n)]
    transitions: list[tuple[str, str, str]] = []
    for j, slot in enumerate(slots):
        for a in slot.alternatives:
            transitions.append((s(j), a, t(j)))
        transitions.append((t(j), LAMBDA, s(j)))
        if slot.optional:
            transitions.append((s(j), LAMBDA, t(j)))
        if j + 1 < n:
            transitions.append((t(j), LAMBDA, s(j + 1)))
    return _build("ENFA", profile, states, transitions, s(0), [t(n - 1)])


BUILDERS = {"DFA": build_dfa, "NFA": build_nfa, "ENFA": build_enfa}


def build_automaton(profile: Profile, kind: str | None = None) -> AutomatonSpec:
    return BUILDERS[kind or profile.construction](profile)


@dataclass
class ProfileResult:
    profile: str
    title: str
    automaton_kind: str
    sequence: list[str]
    accepted: bool
    missing: list[str]

    @property
    def status(self) -> str:
        return "ACCEPTED" if self.accepted else "REJECTED"


class Recognizer:
    """Classifies a normalized token list against every profile."""

    def __init__(self, profiles: dict[str, Profile] | None = None) -> None:
        self.profiles = profiles or PROFILES
        self.automata = {k: build_automaton(p) for k, p in self.profiles.items()}

    def evaluate(self, tokens: list[str], profile_key: str) -> ProfileResult:
        profile = self.profiles[profile_key]
        spec = self.automata[profile_key]
        sequence = profile.canonical_sequence(tokens)
        accepted = bool(sequence) and spec.automaton.accepts(
            [Symbol(t) for t in sequence])
        missing = [s.description for s in profile.missing_requirements(sequence)]
        return ProfileResult(profile.key, profile.title, spec.kind,
                             sequence, accepted, missing)

    def classify(self, tokens: list[str]) -> list[ProfileResult]:
        return [self.evaluate(tokens, key) for key in self.profiles]
