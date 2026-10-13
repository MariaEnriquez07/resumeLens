# Stage 3 — Qualification-pattern recognition with finite automata

Implementation: `resumelens/recognition.py` (pyformlang
`DeterministicFiniteAutomaton`, `NondeterministicFiniteAutomaton`, `EpsilonNFA`).
Complete 5-tuples of the four automata (Q, Σ, δ table, q0, F, type
justification, pattern): [`generated/automata.md`](generated/automata.md).

## Input alphabet

Σ of each automaton = the canonical tokens of the profile (the output of the
Stage 2 transducers). A résumé is a **word over Σ**: its canonical sequence,
e.g. `JAVASCRIPT REACT NODE_JS POSTGRESQL GIT`.

Using whole tokens as symbols (instead of characters) is a deliberate
abstraction level: Stage 2 already solved how each skill is written, so Stage 3
only models *which combinations* of qualifications form a profile.

Before running the automaton, the tokens are **filtered** to the profile
alphabet and **sorted** in the profile order (`Profile.canonical_sequence`).
That is why a linear automaton is enough: it never has to deal with the order
in which the candidate wrote the skills, nor with skills of other profiles.

## Profile language

Each profile is a list of requirements in a fixed order. A required one appears
one or more times (⁺); an optional one zero or more times (*). Example
(ML Engineer):

```
PYTHON⁺ (PANDAS|NUMPY)⁺ (SCIKIT_LEARN|TENSORFLOW|PYTORCH)⁺ ML_MODELING* (SQL|POSTGRESQL|MYSQL)⁺ GIT⁺
```

This is a regular expression over tokens, so the language is regular and a
finite automaton recognises it.

## The four automata

Each automaton is written **by hand** in `recognition.py` as a list of
transitions; each line of code is one arrow of its diagram:

```python
arrows("q0", ("JAVASCRIPT", "TYPESCRIPT"), "q1")   # q0 --JAVASCRIPT|TYPESCRIPT--> q1
```

| Profile | Type | \|Q\| | Final states |
|---|---|---|---|
| Full Stack Developer | DFA | 7 | {q6} |
| Machine Learning Engineer | NFA | 7 | {q6} |
| DevOps Engineer | ε-NFA | 9 | {q8} |
| Data Analyst | DFA | 6 | {q4, q5} |

The three types seen in the course are used. All four follow the same idea: a
chain of states, one per requirement; the state qi means "the first i
requirements are satisfied".

### Full Stack Developer — DFA

![Full Stack DFA](diagrams/FULL_STACK_DEVELOPER_DFA.svg)

* q0 —JS/TS→ q1 —framework→ q2 —backend→ q3 —REST_API→ q4 —database→ q5 —GIT→ q6.
* **Repetition**: a self-loop on each state (q5 —MONGODB→ q5 accepts a second
  database).
* **Optional requirement (REST API)**: a direct arrow q3 —database→ q5 skips q4.

**Why it is a DFA:** there are no λ-transitions and every pair (q, a) has at
most one next state. δ is partial; every missing pair goes to an implicit dead
state that rejects (to have the total function δ : Q × Σ → Q of the course
definition, add a state qd with all the missing arrows and a self-loop on every
symbol; the language does not change).

### Data Analyst — DFA

![Data Analyst DFA](diagrams/DATA_ANALYST_DFA.svg)

Same construction. The optional requirement (statistics) is the last one, so
both q4 (without statistics) and q5 (with statistics) are accepting states.

### Machine Learning Engineer — NFA

![ML Engineer NFA](diagrams/MACHINE_LEARNING_ENGINEER_NFA.svg)

When the automaton reads a symbol of the next requirement it **guesses**:

* more symbols of that requirement will follow → it **stays** (self-loop), or
* that was the last one → it **advances**.

So δ(q0, PYTHON) = {q0, q1}, δ(q1, PANDAS) = {q1, q2}, and so on. The optional
requirement ML_MODELING is skipped with δ(q3, SQL) = {q4, q5}.

**Why it is an NFA:** δ : Q × Σ → ℘(Q) and there are pairs with two next states,
e.g. δ(q0, PYTHON) = {q0, q1}. There are no λ-transitions. A word is accepted if
**at least one** of the possible computations ends in q6.

### DevOps Engineer — ε-NFA

![DevOps ε-NFA](diagrams/DEVOPS_ENGINEER_ENFA.svg)

The same chain as a DFA, but the optional requirement (infrastructure as code:
Terraform or Ansible) is skipped with a **λ-transition** q6 —λ→ q7 (dashed
arrow): the automaton moves to q7 without reading any symbol.

**Why it is an ε-NFA:** δ : Q × (Σ ∪ {λ}) → ℘(Q) and it has the λ-transition
δ(q6, λ) = {q7}.

## Worked examples

**Assignment example (ML Engineer, NFA):** input
`PYTHON PANDAS TENSORFLOW POSTGRESQL GIT`.
One accepting computation: q0 —PYTHON→ q1 —PANDAS→ q2 —TENSORFLOW→ q3
—POSTGRESQL→ q5 (skips ML_MODELING) —GIT→ q6 ∈ F → **ACCEPTED**.

**Repetition (Full Stack, DFA):** `TYPESCRIPT ANGULAR SPRING_BOOT REST_API
POSTGRESQL MONGODB GIT`: q0→q1→q2→q3→q4→q5→q5 (loop on MONGODB)→q6 ∈ F.

**λ-transition (DevOps, ε-NFA):** Peter Parker without Terraform would read
`… AWS GIT`: q5 —AWS→ q6 —λ→ q7 —GIT→ q8 ∈ F → **ACCEPTED**.

**Rejection (Full Stack, DFA):** Clark Kent `JAVASCRIPT VUE MYSQL GIT`:
q0→q1→q2, and δ(q2, MYSQL) is not defined (dead state) → **REJECTED**. The
report lists the missing requirement: *Node.js, Express, Django or Spring Boot*.

## Classification

`Recognizer.classify()` runs the four automata on the four canonical sequences
and returns one `ProfileResult` per profile. A résumé may satisfy several
profiles (Bruce Wayne: Full Stack and DevOps) or none (Clark Kent).

## Limitations

* The model is binary (accepted/rejected); it does not measure *how close* a
  candidate is. The list of missing requirements is computed separately.
* Requirements such as "at least 3 years with Kubernetes" relate two pieces of
  information and are not modelled.
* Only explicitly written qualifications count; the automaton cannot infer that
  someone who uses Django knows Python.
* The automata are written by hand; if a profile changes in `profiles.py`, its
  automaton must be updated too (a test checks that both use the same alphabet).
