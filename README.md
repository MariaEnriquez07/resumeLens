# ResumeLens — Formal Language-Based Resume Screening

Integrative Task 1 · Computación y Estructuras Discretas III · Universidad Icesi · 2026-2

ResumeLens processes plain-text resumes and decides whether the qualifications
**explicitly written** in them satisfy formally defined patterns for four
professional profiles. It does **not** rank candidates or make hiring decisions.

| Stage | Formal model | Library | Module |
|---|---|---|---|
| 1. Extraction | Regular expressions | `re` | `resumelens/extraction.py` |
| 2. Normalization | Finite-state transducers | `pyformlang` | `resumelens/normalization.py` |
| 3. Pattern recognition | DFA, NFA, ε-NFA | `pyformlang` | `resumelens/recognition.py` |
| 4. Candidate profile language | Context-free grammar | `textX` | `resumelens/dsl/` |

Supported profiles: **Full Stack Developer**, **Machine Learning Engineer**,
**DevOps Engineer** (team profile, software engineering) and **Data Analyst**
(team profile, AI/data). All four go through the same code; profiles are data
(`resumelens/profiles.py`).

## Team

| Name | Student code | GitHub |
|---|---|---|
| Maria Camila Cordoba | A00412038 | MariaCamila07 |
| Maria Alejandra Enriquez | A00412040 | MariaEnriquez07 |

Team name: `E_` · Course code: 09834 · Group: _

## Requirements

* Python 3.10 or newer
* Graphviz (`dot`) only if you want to regenerate the diagrams

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# full pipeline on one resume (writes JSON, .resume, HTML and Markdown)
python -m resumelens analyze samples/wednesday_addams.txt --out output/

# every sample
python -m resumelens analyze samples/ --out output/

# validate a candidate-profile specification
python -m resumelens validate samples/valid_minimal.resume --html output/minimal.html
python -m resumelens validate samples/invalid/semantic_wrong_category.resume

# list profiles
python -m resumelens profiles

# graphical interface
streamlit run app.py

# tests
python -m pytest

# regenerate formal definitions and diagrams from the code
python tools/generate_docs.py

```
Example output
```
=== wednesday_addams.txt ===
Candidate : Wednesday Addams
Stage 1   : JS, React.js, NodeJS, Postgres, Git
Stage 2   : JAVASCRIPT, REACT, NODE_JS, POSTGRESQL, GIT
Stage 3   :
   ACCEPTED FULL_STACK_DEVELOPER        [DFA] JAVASCRIPT REACT NODE_JS POSTGRESQL GIT
   REJECTED MACHINE_LEARNING_ENGINEER   [NFA] POSTGRESQL GIT
            missing: Python, Pandas or NumPy, Scikit-learn, TensorFlow or PyTorch
   ...
Stage 4   : profile specification validated by the textX grammar
```
#re

```
resumelens/            source code (one module per stage)
  catalog.py           qualification catalog: categories, canonical tokens, variants
  profiles.py          the four profiles (ordered slots)
  extraction.py        Stage 1
  normalization.py     Stage 2
  recognition.py       Stage 3
  dsl/resume.tx        Stage 4 grammar (textX)
  dsl/__init__.py      serializer + semantic validation
  render.py            HTML / Markdown visualization
  pipeline.py, cli.py  orchestration and command line
app.py                 Streamlit UI
samples/               resumes (.txt), valid and invalid specifications (.resume)
tests/                 pytest suite
tools/generate_docs.py generates docs/generated and docs/diagrams from the code
docs/                  design documents (Markdown)

```



