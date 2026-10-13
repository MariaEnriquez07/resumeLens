"""Stage 3 — Qualification-pattern recognition with finite automata.

Each profile has one automaton, written below as an explicit list of
transitions (each line is one arrow of its diagram). The input of an
automaton is the canonical sequence of a résumé: its tokens filtered to the
profile alphabet and sorted in the profile order (``profiles.py``).

    Full Stack Developer        DFA
    Machine Learning Engineer   NFA
    DevOps Engineer             ε-NFA
    Data Analyst                DFA

The three types seen in the course are used. Why each one is of its type is
explained next to it and in ``docs/stage3_automata.md``.
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

from .profiles import PROFILES, Profile

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


def _make(kind: str, profile_key: str, n_states: int,
          transitions: list[tuple[str, str, str]], finals: list[str]) -> AutomatonSpec:
    """Build the pyformlang automaton from an explicit list of transitions."""
    if kind == "DFA":
        fa = DeterministicFiniteAutomaton()
    elif kind == "NFA":
        fa = NondeterministicFiniteAutomaton()
    else:
        fa = EpsilonNFA()
    for src, sym, dst in transitions:
        symbol = Epsilon() if sym == LAMBDA else Symbol(sym)
        fa.add_transition(State(src), symbol, State(dst))
    fa.add_start_state(State("q0"))
    for f in finals:
        fa.add_final_state(State(f))
    states = [f"q{i}" for i in range(n_states)]
    alphabet = PROFILES[profile_key].alphabet
    return AutomatonSpec(profile_key, kind, states, alphabet, transitions, "q0", finals, fa)


def arrows(src: str, symbols: tuple[str, ...], dst: str) -> list[tuple[str, str, str]]:
    """One arrow of the diagram labelled with several symbols."""
    return [(src, a, dst) for a in symbols]


# --------------------------------------------------------------------------- #
# Full Stack Developer — DFA
#   JS/TS⁺ · framework⁺ · backend⁺ · REST_API* · database⁺ · GIT⁺
# Each state has at most one transition per symbol and there is no λ:
# it is a DFA. Repetition = self-loop; the optional REST_API is skipped by
# the direct arrow q3 → q5.
# --------------------------------------------------------------------------- #

def full_stack_dfa() -> AutomatonSpec:
    lang = ("JAVASCRIPT", "TYPESCRIPT")
    front = ("REACT", "ANGULAR", "VUE")
    back = ("NODE_JS", "EXPRESS", "DJANGO", "SPRING_BOOT")
    api = ("REST_API",)
    db = ("SQL", "NOSQL", "POSTGRESQL", "MYSQL", "MONGODB", "SQLITE")
    git = ("GIT",)
    t = (arrows("q0", lang, "q1") + arrows("q1", lang, "q1")
         + arrows("q1", front, "q2") + arrows("q2", front, "q2")
         + arrows("q2", back, "q3") + arrows("q3", back, "q3")
         + arrows("q3", api, "q4") + arrows("q4", api, "q4")
         + arrows("q3", db, "q5")                      # skips the optional API
         + arrows("q4", db, "q5") + arrows("q5", db, "q5")
         + arrows("q5", git, "q6") + arrows("q6", git, "q6"))
    return _make("DFA", "FULL_STACK_DEVELOPER", 7, t, ["q6"])


# --------------------------------------------------------------------------- #
# Machine Learning Engineer — NFA
#   PYTHON⁺ · (PANDAS|NUMPY)⁺ · (SCIKIT_LEARN|TENSORFLOW|PYTORCH)⁺
#   · ML_MODELING* · database⁺ · GIT⁺
# From qi, when the automaton reads a symbol of the next requirement it
# GUESSES: either more symbols of that requirement follow (it stays in qi)
# or that was the last one (it moves to qi+1). So δ(q0, PYTHON) = {q0, q1}:
# one pair with two next states, which makes it an NFA.
# --------------------------------------------------------------------------- #

def ml_engineer_nfa() -> AutomatonSpec:
    py = ("PYTHON",)
    data = ("PANDAS", "NUMPY")
    fw = ("SCIKIT_LEARN", "TENSORFLOW", "PYTORCH")
    model = ("ML_MODELING",)
    db = ("SQL", "POSTGRESQL", "MYSQL")
    git = ("GIT",)
    t = (arrows("q0", py, "q0") + arrows("q0", py, "q1")
         + arrows("q1", data, "q1") + arrows("q1", data, "q2")
         + arrows("q2", fw, "q2") + arrows("q2", fw, "q3")
         + arrows("q3", model, "q3") + arrows("q3", model, "q4")
         + arrows("q3", db, "q4") + arrows("q3", db, "q5")    # skips ML_MODELING
         + arrows("q4", db, "q4") + arrows("q4", db, "q5")
         + arrows("q5", git, "q5") + arrows("q5", git, "q6"))
    return _make("NFA", "MACHINE_LEARNING_ENGINEER", 7, t, ["q6"])


# --------------------------------------------------------------------------- #
# DevOps Engineer — ε-NFA
#   LINUX⁺ · (BASH|PYTHON)⁺ · DOCKER⁺ · KUBERNETES⁺ · CI/CD⁺ · cloud⁺
#   · (TERRAFORM|ANSIBLE)* · GIT⁺
# Same chain as a DFA, but the optional infrastructure-as-code requirement is
# skipped with a λ-transition q6 → q7 (it moves without reading a symbol).
# That λ-transition makes it an ε-NFA.
# --------------------------------------------------------------------------- #

def devops_enfa() -> AutomatonSpec:
    linux = ("LINUX",)
    script = ("BASH", "PYTHON")
    docker = ("DOCKER",)
    k8s = ("KUBERNETES",)
    cicd = ("JENKINS", "GITHUB_ACTIONS", "GITLAB_CI")
    cloud = ("AWS", "AZURE", "GCP")
    iac = ("TERRAFORM", "ANSIBLE")
    git = ("GIT",)
    t = (arrows("q0", linux, "q1") + arrows("q1", linux, "q1")
         + arrows("q1", script, "q2") + arrows("q2", script, "q2")
         + arrows("q2", docker, "q3") + arrows("q3", docker, "q3")
         + arrows("q3", k8s, "q4") + arrows("q4", k8s, "q4")
         + arrows("q4", cicd, "q5") + arrows("q5", cicd, "q5")
         + arrows("q5", cloud, "q6") + arrows("q6", cloud, "q6")
         + arrows("q6", iac, "q7") + arrows("q7", iac, "q7")
         + [("q6", LAMBDA, "q7")]                          # skips IaC
         + arrows("q7", git, "q8") + arrows("q8", git, "q8"))
    return _make("ENFA", "DEVOPS_ENGINEER", 9, t, ["q8"])


# --------------------------------------------------------------------------- #
# Data Analyst — DFA
#   SQL⁺ · EXCEL⁺ · (POWER_BI|TABLEAU)⁺ · (PYTHON|R)⁺ · STATISTICS*
# The optional requirement is the last one, so q4 (without statistics) and
# q5 (with statistics) are both accepting states.
# --------------------------------------------------------------------------- #

def data_analyst_dfa() -> AutomatonSpec:
    query = ("SQL", "MYSQL", "POSTGRESQL")
    excel = ("EXCEL",)
    viz = ("POWER_BI", "TABLEAU")
    prog = ("PYTHON", "R")
    stats = ("STATISTICS",)
    t = (arrows("q0", query, "q1") + arrows("q1", query, "q1")
         + arrows("q1", excel, "q2") + arrows("q2", excel, "q2")
         + arrows("q2", viz, "q3") + arrows("q3", viz, "q3")
         + arrows("q3", prog, "q4") + arrows("q4", prog, "q4")
         + arrows("q4", stats, "q5") + arrows("q5", stats, "q5"))
    return _make("DFA", "DATA_ANALYST", 6, t, ["q4", "q5"])


AUTOMATA = {
    "FULL_STACK_DEVELOPER": full_stack_dfa,
    "MACHINE_LEARNING_ENGINEER": ml_engineer_nfa,
    "DEVOPS_ENGINEER": devops_enfa,
    "DATA_ANALYST": data_analyst_dfa,
}


def build_automaton(profile: Profile) -> AutomatonSpec:
    """The automaton that models ``profile``."""
    return AUTOMATA[profile.key]()


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
