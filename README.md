# ResumeLens

ResumeLens reads plain-text résumés and checks whether the qualifications
written in them satisfy the pattern of four profiles: Full Stack Developer,
Machine Learning Engineer, DevOps Engineer and Data Analyst. It does not rank
candidates or make hiring decisions.

| Stage | Formal model | Module |
|---|---|---|
| 1. Extraction | Regular expressions (`re`) | `resumelens/extraction.py` |
| 2. Normalization | Finite-state transducers (`pyformlang`) | `resumelens/normalization.py` |
| 3. Recognition | DFA, NFA, ε-NFA (`pyformlang`) | `resumelens/recognition.py` |
| 4. Profile language | Context-free grammar (`textX`) | `resumelens/dsl/` |

## Team

| Name | Student code | GitHub |
|---|---|---|
| Maria Camila Cordoba | A00412038 | MariaCamila07 |
| Maria Alejandra Enriquez | A00412040 | MariaEnriquez07 |

Team: `E_` · Course code: 09834 · Group: _

IDE: Visual Studio Code · Python 3.12 · Windows

## How to run

Open the `resumeLens` folder in Visual Studio Code and open a terminal
(**Terminal → New Terminal**). Run every command from the project root (the
folder that contains this README).

### 1. Install the dependencies (once)

```powershell
pip install -r requirements.txt
```

Optional, to install them in a virtual environment instead:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1          # Windows (PowerShell / VS Code terminal)
# source .venv/bin/activate         # macOS, Linux or Git Bash
pip install -r requirements.txt
```

If PowerShell says that running scripts is disabled, run once
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` and try again.

### 2. Use the program

```powershell
# full pipeline on one résumé (writes JSON, .resume and HTML in output/)
python -m resumelens analyze samples/wednesday_addams.txt --out output/

# every sample résumé
python -m resumelens analyze samples/ --out output/

# validate a candidate-profile specification (.resume)
python -m resumelens validate samples/valid_minimal.resume --html output/minimal.html
python -m resumelens validate samples/invalid/semantic_wrong_category.resume   # rejected on purpose

# graphical interface (opens in the browser; stop it with Ctrl + C)
streamlit run app.py

# tests
python -m pytest
```

### 3. Regenerate the formal definitions and diagrams (optional)

```powershell
python tools/generate_docs.py
```

Rewrites `docs/generated/` (7-tuples and 5-tuples) and `docs/diagrams/`.
The `.svg` images need [Graphviz](https://graphviz.org/download/) installed.

## Documentation

Design documents are in [`docs/`](docs/): profiles, module design, one document
per stage (regular expressions, transducers, automata, grammar), the generated
7-tuples, 5-tuples and diagrams, and the test cases.




