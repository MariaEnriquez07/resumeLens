# Literature review (draft)

## 1. Résumé parsing and information extraction

Résumé screening is an information-extraction problem: finding entities
(names, contact data, degrees, skills) in semi-structured text. Early work
combined rules and statistical models in cascades, e.g. Yu, Guan and Zhou
(2005) segment a résumé into blocks and then extract fields inside each block.
Later work uses sequence labelling (CRF, BiLSTM-CRF) and transformer models
(BERT-based NER). These approaches are more robust to unseen formats, but they
need labelled data and are not explainable in formal terms.

**Position of ResumeLens:** a transparent, rule-based pipeline in which every
decision is traceable to a regular expression, a transducer transition or an
automaton state. We trade recall on unseen formats for explainability and for
guarantees that can be proven (determinism, equivalence of automata, grammar
validity).

## 2. Regular expressions for text extraction

Regular expressions describe regular languages and are the standard tool for
extracting lexical patterns such as e-mails, phone numbers and dates
(Friedl, *Mastering Regular Expressions*, 3rd ed., O'Reilly, 2006). Modern
engines (Python `re`) add look-arounds and lazy quantifiers; look-arounds do not
increase the class of languages recognised in this bounded use, but make the
patterns easier to write.

## 3. Finite-state transducers for normalization

Finite-state transducers are widely used in natural-language processing for
morphology, spelling normalisation and text normalisation
(Mohri, 1997, "Finite-state transducers in language and speech processing",
*Computational Linguistics* 23(2); Beesley and Karttunen, *Finite State
Morphology*, CSLI, 2003). Jurafsky and Martin (*Speech and Language
Processing*) present FSTs for morphological parsing and text normalisation.
A dictionary of variants compiled into a trie-shaped transducer is the
classical way of mapping many surface forms to one lemma.

## 4. Finite automata

Hopcroft, Motwani and Ullman (*Introduction to Automata Theory, Languages, and
Computation*) and Sipser (*Introduction to the Theory of Computation*) give the
definitions of DFA, NFA and ε-NFA used in this project, the subset construction
and the equivalence of the three models, which our tests check experimentally
with pyformlang.

## 5. Context-free grammars and DSLs

Domain-specific languages let domain data be written and validated with a
precise syntax (Fowler, *Domain-Specific Languages*, Addison-Wesley, 2010).
textX (Dejanović, Vaderna, Milosavljević and Vuković, 2017, "TextX: A Python
tool for Domain-Specific Languages implementation", *Knowledge-Based Systems*)
builds a parser and a meta-model from a single grammar description, based on
the Arpeggio PEG parser.

## 6. Tools

* **pyformlang** (Romero, 2021, "Pyformlang: An Educational Library for Formal
  Language Manipulation", SIGCSE) — regular expressions, finite automata, FSTs
  and CFGs in Python.
* **Python `re`** — standard-library regular expressions.
* **textX** — DSL implementation in Python.

## 7. Fairness and responsible use

Automated screening can reproduce bias; this is why ResumeLens explicitly
**does not rank candidates or make hiring decisions** and only reports whether
explicitly written qualifications satisfy explicit patterns. Its decisions are
fully explainable: every rejection lists the missing requirements.

## Gaps this project addresses

1. Most résumé-parsing systems are statistical black boxes; ResumeLens shows a
   fully formal, explainable alternative.
2. Normalization of skill names is usually done with ad-hoc dictionaries;
   modelling it as a transducer makes its behaviour provable (determinism,
   one output per input).
3. Profile requirements are rarely formalised; describing them as regular
   languages makes them testable and comparable.