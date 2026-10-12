"""Stage 3 — finite automata (test cases TC-A*)."""

import itertools

import pytest
from pyformlang.finite_automaton import Symbol

from resumelens.profiles import PROFILES
from resumelens.recognition import LAMBDA, Recognizer, build_automaton

S = lambda seq: [Symbol(t) for t in seq]  # noqa: E731


@pytest.fixture(scope="module")
def recognizer():
    return Recognizer()


# TC-A01 — the declared type is justified by the definition
@pytest.mark.parametrize("key", PROFILES)
def test_declared_type(key):
    spec = build_automaton(PROFILES[key])
    delta = spec.delta()
    has_lambda = any(a == LAMBDA for (_, a) in delta)
    has_multi = any(len(d) > 1 for d in delta.values())
    if spec.kind == "DFA":
        assert not has_lambda and not has_multi
        assert spec.automaton.is_deterministic()
    elif spec.kind == "NFA":
        assert not has_lambda and has_multi
    else:
        assert has_lambda


def test_one_of_each_kind_is_used():
    kinds = {p.construction for p in PROFILES.values()}
    assert kinds == {"DFA", "NFA", "ENFA"}


# TC-A02 — example of the assignment
def test_assignment_example_ml(recognizer):
    r = recognizer.evaluate(["PYTHON", "PANDAS", "TENSORFLOW", "POSTGRESQL", "GIT"],
                            "MACHINE_LEARNING_ENGINEER")
    assert r.accepted


# TC-A03 — accepted / rejected sequences per profile (already in canonical order)
CASES = [
    ("FULL_STACK_DEVELOPER", ["JAVASCRIPT", "REACT", "NODE_JS", "POSTGRESQL", "GIT"], True),
    ("FULL_STACK_DEVELOPER", ["TYPESCRIPT", "ANGULAR", "SPRING_BOOT", "REST_API", "MONGODB", "GIT"], True),
    ("FULL_STACK_DEVELOPER", ["JAVASCRIPT", "REACT", "POSTGRESQL", "GIT"], False),     # no backend
    ("FULL_STACK_DEVELOPER", ["JAVASCRIPT", "TYPESCRIPT", "REACT", "VUE", "NODE_JS",
                              "DJANGO", "SQL", "MONGODB", "GIT"], True),                # repetitions
    ("MACHINE_LEARNING_ENGINEER", ["PYTHON", "NUMPY", "PYTORCH", "ML_MODELING", "SQL", "GIT"], True),
    ("MACHINE_LEARNING_ENGINEER", ["PYTHON", "PANDAS", "SQL", "GIT"], False),          # no framework
    ("DEVOPS_ENGINEER", ["LINUX", "BASH", "DOCKER", "KUBERNETES", "JENKINS", "AWS", "GIT"], True),
    ("DEVOPS_ENGINEER", ["LINUX", "BASH", "DOCKER", "KUBERNETES", "JENKINS", "AWS",
                         "TERRAFORM", "ANSIBLE", "GIT"], True),
    ("DEVOPS_ENGINEER", ["LINUX", "BASH", "DOCKER", "JENKINS", "AWS", "GIT"], False),  # no k8s
    ("DATA_ANALYST", ["SQL", "EXCEL", "TABLEAU", "PYTHON"], True),
    ("DATA_ANALYST", ["SQL", "EXCEL", "POWER_BI", "R", "STATISTICS"], True),
    ("DATA_ANALYST", ["SQL", "POWER_BI", "PYTHON"], False),                           # no Excel
]


@pytest.mark.parametrize("key,seq,expected", CASES)
def test_sequences(key, seq, expected):
    fa = build_automaton(PROFILES[key]).automaton
    assert fa.accepts(S(seq)) is expected


# TC-A04 — the automata depend on the order; the sorting stage removes that dependence
def test_order_matters_for_the_automaton_but_not_for_the_pipeline(recognizer):
    unsorted = ["GIT", "NODE_JS", "JAVASCRIPT", "POSTGRESQL", "REACT"]
    fa = build_automaton(PROFILES["FULL_STACK_DEVELOPER"]).automaton
    assert not fa.accepts(S(unsorted))
    for perm in itertools.islice(itertools.permutations(unsorted), 30):
        assert recognizer.evaluate(list(perm), "FULL_STACK_DEVELOPER").accepted


# TC-A05 — empty input and foreign tokens
@pytest.mark.parametrize("key", PROFILES)
def test_empty_sequence_rejected(recognizer, key):
    assert not recognizer.evaluate([], key).accepted


def test_foreign_tokens_are_filtered(recognizer):
    r = recognizer.evaluate(["SQL", "EXCEL", "TABLEAU", "PYTHON", "DOCKER", "REACT"],
                            "DATA_ANALYST")
    assert r.accepted and r.sequence == ["SQL", "EXCEL", "TABLEAU", "PYTHON"]


def test_missing_requirements_reported(recognizer):
    r = recognizer.evaluate(["JAVASCRIPT", "REACT", "GIT"], "FULL_STACK_DEVELOPER")
    assert r.missing == ["Node.js, Express, Django or Spring Boot", "SQL or NoSQL database"]
