# Test design

Run everything with `python -m pytest` (≈ 260 test cases, a few seconds).
Many cases are generated automatically from the catalog with `pytest.mark.parametrize`.
Each test function is tagged in its docstring/comment with the IDs below.

## Scenarios (end-to-end, `tests/test_pipeline.py`)

| ID | Scenario | Input | Expected result |
|---|---|---|---|
| TC-P01 | Assignment example, Full Stack | `samples/wednesday_addams.txt` | Full Stack ACCEPTED only |
| TC-P02 | Assignment example, ML Engineer | `samples/mary_jane_watson.txt` | ML Engineer ACCEPTED only |
| TC-P03 | Team profile, DevOps, complete résumé (contact, jobs, education) | `samples/peter_parker.txt` | DevOps ACCEPTED only |
| TC-P04 | Team profile, Data Analyst, case-sensitive `R` | `samples/gwen_stacy.txt` | Data Analyst ACCEPTED only |
| TC-P05 | Candidate satisfying two profiles | `samples/bruce_wayne.txt` | Full Stack and DevOps ACCEPTED |
| TC-P06 | Incomplete profile (no backend) | `samples/clark_kent.txt` | all REJECTED, missing backend reported |
| TC-P07 | Messy spelling (lower case `javascript`, `No-SQL`, `github`, `k8s`) | `samples/diana_prince.txt` | Full Stack ACCEPTED |
| TC-P08 | Spaced variants (`Py Torch`, `Tensor Flow`) and two degrees | `samples/tony_stark.txt` | ML Engineer ACCEPTED |
| TC-P09 | Résumé with no skills | inline text | no profile accepted, valid spec generated |
| TC-P10 | Outputs are persisted | Wednesday | 6 non-empty files |
| TC-P11 | CLI exit codes | valid / syntax / semantic | 0 / 2 / 3 |

## Stage 1 — regular expressions (`tests/test_extraction.py`)

| ID | What is checked | Examples |
|---|---|---|
| TC-E01 | Assignment example is extracted exactly | `JS, React.js, NodeJS, Postgres, Git` |
| TC-E02 | Contact: valid and invalid e-mails and phones, links | `test.example.com` ✗, `(602) 555-0199` ✓, `(2019 - 2022)` ✗ |
| TC-E03 | Jobs, degrees, several degrees, `yrs` | Peter Parker, Tony Stark |
| TC-E04 | Text is kept as written (no normalization) | `Py Torch` stays `Py Torch` |
| TC-E05 | Word boundaries `\b` and longest alternative first | no `js` in `Node.js`, no `SQL` in `PostgreSQL` |
| TC-E06 | Order of the categories (ML_DATA before LANGUAGES) | `Py Torch` → ML_DATA |
| TC-E07 | False positives avoided | "the rest of the team", "excel at", "express your ideas", URLs |
| TC-E08 | Every catalog variant is matched by its category pattern | 71 variants |

## Stage 2 — transducers (`tests/test_normalization.py`)

| ID | What is checked |
|---|---|
| TC-N01 | The 16 transformations of the assignment table |
| TC-N02 | 9 transformations proposed by the team (DevOps, Data Analyst) |
| TC-N03 | Every variant in lower, UPPER and Title case produces exactly one output |
| TC-N04 | Unknown strings and incomplete prefixes produce no output (`Reac`, `HTML`, empty) |
| TC-N05 | Every transducer is deterministic; q0 and F = {qf} |
| TC-N06 | Duplicates removed; the assignment sorting example gives `JAVASCRIPT, REACT, NODE_JS, POSTGRESQL, GIT`; unrecognized strings reported |

## Stage 3 — automata (`tests/test_recognition.py`)

| ID | What is checked |
|---|---|
| TC-A01 | The declared type matches the definition (DFA: no λ and at most one successor; NFA: some pair with several successors; ε-NFA: λ-transitions), the three types are used, and each hand-written automaton uses exactly the alphabet of its profile |
| TC-A02 | Assignment example `PYTHON, PANDAS, TENSORFLOW, POSTGRESQL, GIT` is ACCEPTED |
| TC-A03 | 12 accepted/rejected sequences (repetition, optional present/absent, missing slot) |
| TC-A04 | The automaton depends on order; the sorting stage removes the dependence (30 permutations) |
| TC-A05 | Empty sequence rejected, foreign tokens filtered, missing requirements reported |

## Stage 4 — grammar (`tests/test_dsl.py`)

| ID | What is checked |
|---|---|
| TC-G01 | Valid specifications parse and produce the expected model structure |
| TC-G02 | 5 lexical/syntactic violations raise `TextXSyntaxError` (missing `;`, bad e-mail, lower-case skill, unknown profile, unknown status) |
| TC-G03 | 3 semantic violations raise `TextXSemanticError` (duplicated skill, skill in the wrong category, accepted profile without sequence) |
| TC-G04 | Repeated elements (2 degrees, 2 jobs) |
| TC-G05 | HTML is generated and escapes user text |

## UI (`tests/test_ui.py`)

Streamlit `AppTest`: the app loads, runs the pipeline for a sample and
validates a specification without exceptions.