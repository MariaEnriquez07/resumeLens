# Professional profiles

ResumeLens supports four profiles. Two are given by the assignment (Full Stack
Developer, Machine Learning Engineer) and two were defined by the team: **DevOps
Engineer** (software engineering) and **Data Analyst** (AI / data).

All four are processed by the *same* code: a profile is **data** (an ordered
list of slots in `resumelens/profiles.py`), and the automaton of each profile is
built by the same generic constructions (`resumelens/recognition.py`).

## How a profile is defined

A profile is an ordered list of **slots**. A slot is one requirement that can be
satisfied by one or more canonical tokens from a set of alternatives (the "or"
in the job description). A slot can be **optional**.

The slot order is the **canonical order** of the profile. Before a résumé
reaches the automaton, Stage 2 keeps only the tokens of the profile alphabet and
sorts them by slot. This is what makes the result independent of the order in
which the candidate wrote the skills.

For slots S1..Sn with alternative sets A1..An the profile language is

    L = X1 X2 … Xn,   Xi = Ai⁺ (required)   or   Xi = Ai* (optional)

## 1. Full Stack Developer — DFA

| # | Slot | Alternatives | Required |
|---|---|---|---|
| 1 | frontend_language | JAVASCRIPT, TYPESCRIPT | yes |
| 2 | frontend_framework | REACT, ANGULAR, VUE | yes |
| 3 | backend | NODE_JS, EXPRESS, DJANGO, SPRING_BOOT | yes |
| 4 | api | REST_API | optional |
| 5 | database | SQL, NOSQL, POSTGRESQL, MYSQL, MONGODB, SQLITE | yes |
| 6 | version_control | GIT | yes |

REST APIs are optional because the example résumé of the assignment (Wednesday
Addams) does not mention them and is expected to be accepted.

## 2. Machine Learning Engineer — NFA

| # | Slot | Alternatives | Required |
|---|---|---|---|
| 1 | language | PYTHON | yes |
| 2 | data_processing | PANDAS, NUMPY | yes |
| 3 | ml_framework | SCIKIT_LEARN, TENSORFLOW, PYTORCH | yes |
| 4 | ml_modeling | ML_MODELING | optional |
| 5 | database | SQL, POSTGRESQL, MYSQL | yes |
| 6 | version_control | GIT | yes |

Scikit-learn, TensorFlow and PyTorch share a slot, following the example
automaton of the assignment (q2 → q3 on any of the three).

## 3. DevOps Engineer — ε-NFA (team profile, software engineering)

| # | Slot | Alternatives | Required |
|---|---|---|---|
| 1 | operating_system | LINUX | yes |
| 2 | scripting | BASH, PYTHON | yes |
| 3 | containers | DOCKER | yes |
| 4 | orchestration | KUBERNETES | yes |
| 5 | ci_cd | JENKINS, GITHUB_ACTIONS, GITLAB_CI | yes |
| 6 | cloud | AWS, AZURE, GCP | yes |
| 7 | infrastructure_as_code | TERRAFORM, ANSIBLE | optional |
| 8 | version_control | GIT | yes |

Variants normalized for this profile: `k8s` → KUBERNETES, `Ubuntu` → LINUX,
`Amazon Web Services` → AWS, `Google Cloud` → GCP, `GitLab-CI` → GITLAB_CI.

## 4. Data Analyst — DFA (team profile, AI / data)

| # | Slot | Alternatives | Required |
|---|---|---|---|
| 1 | querying | SQL, MYSQL, POSTGRESQL | yes |
| 2 | spreadsheets | EXCEL | yes |
| 3 | visualization | POWER_BI, TABLEAU | yes |
| 4 | programming | PYTHON, R | yes |
| 5 | statistics | STATISTICS | optional |

Variants normalized for this profile: `PowerBI` → POWER_BI,
`MS Excel` → EXCEL, `GitHub` → GIT.

## Design decisions

* **Disjoint slots.** Inside one profile a token belongs to at most one slot.
  This keeps the DFA construction deterministic.
* **Shared tokens between profiles are allowed** (PYTHON is in three profiles,
  GIT in three). A résumé can therefore satisfy several profiles (see the Bruce
  Wayne scenario: Full Stack + DevOps).
* **Filtering before recognition.** Tokens outside the profile alphabet are
  removed before running the automaton, so a DevOps engineer who also knows
  React is not rejected because of the extra skill.
* **Different automaton types.** Each profile declares an official model so that
  the three kinds seen in the course are used: DFA (Full Stack, Data Analyst),
  NFA (ML Engineer) and ε-NFA (DevOps).
* **Small catalog.** Each qualification has 1–3 variants. This is enough to
  show the normalization problem while keeping the transducers readable.