"""ResumeLens: formal-language-based résumé screening.

Pipeline:
    Stage 1  extraction.py     regular expressions   (Python ``re``)
    Stage 2  normalization.py  finite-state transducers (pyformlang)
    Stage 3  recognition.py    finite automata (DFA / NFA / ε-NFA, pyformlang)
    Stage 4  dsl/              context-free grammar (textX) + HTML rendering
"""

__version__ = "1.0.0"
