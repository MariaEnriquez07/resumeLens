"""Stage 2 — finite-state transducers (test cases TC-N*)."""

import pytest

from resumelens.catalog import CATEGORIES, LEXICON
from resumelens.normalization import END, build_transducer, preprocess
from resumelens.profiles import PROFILES

# TC-N01 — the transformations listed in the assignment
ASSIGNMENT_TABLE = [
    ("JS", "JAVASCRIPT"), ("Javascript", "JAVASCRIPT"),
    ("React.js", "REACT"), ("ReactJS", "REACT"),
    ("NodeJS", "NODE_JS"), ("Node.js", "NODE_JS"),
    ("Postgres", "POSTGRESQL"), ("PostgreSQL", "POSTGRESQL"),
    ("pandas", "PANDAS"),
    ("sklearn", "SCIKIT_LEARN"), ("scikit learn", "SCIKIT_LEARN"),
    ("Scikit-learn", "SCIKIT_LEARN"),
    ("Tensor Flow", "TENSORFLOW"), ("TensorFlow", "TENSORFLOW"),
    ("Py Torch", "PYTORCH"), ("PyTorch", "PYTORCH"),
]


@pytest.mark.parametrize("raw,canonical", ASSIGNMENT_TABLE)
def test_assignment_transformations(normalizer, raw, canonical):
    assert normalizer.translate(raw)[0] == canonical


# TC-N02 — our own transformations (DevOps and Data Analyst profiles)
@pytest.mark.parametrize("raw,canonical", [
    ("k8s", "KUBERNETES"), ("K8S", "KUBERNETES"),
    ("Amazon Web Services", "AWS"), ("Google Cloud", "GCP"),
    ("GitLab-CI", "GITLAB_CI"), ("Ubuntu", "LINUX"),
    ("PowerBI", "POWER_BI"), ("MS Excel", "EXCEL"), ("GitHub", "GIT"),
])
def test_own_transformations(normalizer, raw, canonical):
    assert normalizer.translate(raw)[0] == canonical


# TC-N03 — every variant in the catalog, in lower, UPPER and Title case
@pytest.mark.parametrize("category,variant,canonical", [
    (c, v, tok) for c, entries in LEXICON.items() for tok, vs in entries.items() for v in vs
])
def test_every_variant_every_case(category, variant, canonical):
    spec = build_transducer(category)
    for form in (variant, variant.upper(), variant.title()):
        out = list(spec.fst.translate(list(form) + [END]))
        assert out == [[canonical]], form


# TC-N04 — rejection of unknown strings and of incomplete prefixes
@pytest.mark.parametrize("raw", ["HTML", "Reac", "Kubernete", "Photoshop", ""])
def test_unknown_strings(normalizer, raw):
    assert normalizer.translate(raw) is None


# TC-N05 — the transducers are deterministic (at most one transition per (q, a))
@pytest.mark.parametrize("category", CATEGORIES)
def test_transducers_are_deterministic(category):
    spec = build_transducer(category)
    pairs = [(src, sym) for src, sym, _, _ in spec.transitions]
    assert len(pairs) == len(set(pairs))
    assert spec.finals == ["qf"] and spec.start == "q0"


def test_preprocess_whitespace_and_punctuation():
    assert preprocess("  Tensor   Flow. ") == "Tensor Flow"


# TC-N06 — normalization removes duplicates and sorting is profile-driven
def test_duplicates_and_global_order(normalizer):
    res = normalizer.normalize(["Git", "NodeJS", "JS", "Postgres", "React.js", "javascript"])
    assert res.tokens == ["JAVASCRIPT", "REACT", "NODE_JS", "POSTGRESQL", "GIT"]


def test_assignment_sorting_example(normalizer):
    """Git, NodeJS, JS, Postgres, React.js -> JAVASCRIPT, REACT, NODE_JS, POSTGRESQL, GIT"""
    res = normalizer.normalize(["Git", "NodeJS", "JS", "Postgres", "React.js"])
    seq = PROFILES["FULL_STACK_DEVELOPER"].canonical_sequence(res.tokens)
    assert seq == ["JAVASCRIPT", "REACT", "NODE_JS", "POSTGRESQL", "GIT"]


def test_unrecognized_are_reported(normalizer):
    res = normalizer.normalize(["Git", "Photoshop"])
    assert res.tokens == ["GIT"] and res.unrecognized == ["Photoshop"]