# Stage 1 — Information extraction with regular expressions

Implementation: `resumelens/extraction.py` (Python `re`). Output:
`ExtractionResult`, saved as `<name>.extraction.json`.

This stage **only finds** candidate strings. It keeps them exactly as written
(`Py Torch` stays `Py Torch`); equivalence is decided in Stage 2.

Notation: Σ is the set of Unicode characters; `\d` = digits, `\w` = letters,
digits and `_`, `\s` = whitespace.

## Contact information

### E-mail
```
[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+
```
Language: a non-empty local part over letters, digits and `._%+-`, the symbol
`@`, a domain label, and **one or more** `.label` groups. Accepts
`a.b+cv@uni.edu.co`; rejects `test.example.com`, `user@`, `@domain.com`.

### Phone
```
(?<![\w+])(?:\+\d{1,3}[\s-]?)?(?:\(\d{1,4}\)[\s-]?)?\d{3}[\s-]?\d{3,4}(?:[\s-]?\d{2,4})?(?![\w])
```
Language: optional country code `+d…`, optional area code in parentheses, then a
group of 3 digits, a group of 3–4 digits and an optional group of 2–4 digits,
separated by at most one space or hyphen. The look-arounds forbid matches glued
to other digits/letters. Accepts `+57 300 123 4567`, `(602) 555-0199`; rejects
year ranges such as `2019 - 2022` (two separators) and `3 years`.

### LinkedIn and GitHub
```
(?:https?://)?(?:www\.)?linkedin\.com/in/[A-Za-z0-9_-]+/?
(?:https?://)?(?:www\.)?github\.com/[A-Za-z0-9_-]+/?
```
Optional scheme and `www.`, fixed domain and path prefix, a user name.

### Name
```
^[ \t]*(W(?:[ \t]+W){1,3})[ \t]*$      W = [A-ZÁÉÍÓÚÑÜ][A-Za-zÁÉÍÓÚÑÜáéíóúñü'’-]+
```
Applied to the **first non-empty line**: 2 to 4 words, each starting with a
capital letter.

## Professional experience

### Years of experience
```
(?P<years>\d{1,2})\+?\s*(?:years?|yrs?)\s+of\s+(?:professional\s+)?experience
(?:\s+(?P<field>(?:in|as|developing|building|with|on|designing|working)\s+[^.\n]+))?
```
(case-insensitive) Language: a 1–2 digit number, optional `+`, the word
`year(s)`/`yr(s)`, `of [professional] experience`, and optionally a field
introduced by a preposition or gerund, up to the end of the sentence.
`3 years of experience developing web applications.` → years = 3,
field = `developing web applications`.

### Jobs
```
^[ \t]*[-*•]?[ \t]*(?P<role>[A-Z][A-Za-z/&+ -]{2,60}?)\s+at\s+(?P<company>[A-Z][A-Za-z0-9&.' -]{1,60}?)\s*
\(\s*(?P<start>(?:19|20)\d{2})\s*[-–]\s*(?P<end>(?:19|20)\d{2}|[Pp]resent|[Aa]ctualidad)\s*\)
```
Language: an optional bullet, a capitalised role, the word `at`, a capitalised
company and a period `(YYYY - YYYY)` or `(YYYY - Present)`.
The lazy quantifiers `{…}?` stop the role at the first ` at `.

## Academic qualifications
```
(?P<level>Ph\.?\s?D\.?|Doctorate|M\.?\s?Sc\.?|Master(?:'s)?(?:\s+of\s+Science)?|
          B\.?\s?Sc\.?|B\.?\s?S\.?|Bachelor(?:'s)?(?:\s+of\s+Science)?|Technologist|Technician)
(?:\s+degree)?\s+(?:in|of)\s+(?P<field>[A-Z][A-Za-zÁÉÍÓÚáéíóúñ &-]+?)
(?:\s*(?:,|\s-\s|\s+at\s+)\s*(?P<institution>[A-Z][A-Za-zÁÉÍÓÚáéíóúñ .&-]+?))?
\s*(?:\(\s*(?P<year>(?:19|20)\d{2})\s*\))?[ \t]*$
```
Language: a degree level (with or without dots), `in`/`of`, a field, an
optional institution after `,`, ` - ` or ` at `, and an optional `(year)` at the
end of the line. `B.Sc. in Systems Engineering, Universidad Icesi (2020)`.

## Qualifications (programming languages, frameworks, databases, tools…)

One pattern per category. Every pattern has the form

```
L = (?<![\w.#+/@&-])  (f1 | f2 | … | fk)  (?![\w#+/@&-]|\.\w)
```

The prefix and suffix are a **custom word boundary**: a match cannot be glued to
letters, digits or to the characters `. # + / @ & -` that appear inside skill
names. This is why `js` is not found inside `Node.js`, `sql` is not found inside
`PostgreSQL`, and `react` is not found inside `React.js`.

| Category | Fragments (case-insensitive unless marked `(?-i:…)`) |
|---|---|
| LANGUAGES | `javascript`, `js`, `typescript`, `ts`, `python`, `py`, `bash`, `(?-i:Shell)`, `(?-i:R)` |
| FRAMEWORKS | `react(?:\.js\|js)?`, `angular(?:js)?`, `vue(?:\.js)?`, `node(?:\.js\|js)?`, `express\.js`, `(?-i:Express)`, `django`, `spring\s?boot`, `rest\s+apis?`, `(?-i:REST)` |
| DATABASES | `no-?sql`, `postgre(?:sql\|s)`, `mysql`, `mongo(?:db)?`, `sqlite`, `sql` |
| ML_DATA | `pandas`, `numpy`, `scikit[\s-]learn`, `sklearn`, `tensor\s?flow`, `py\s?torch`, `machine\s+learning`, `predictive\s+models` |
| DEVOPS_CLOUD | `linux`, `ubuntu`, `docker`, `kubernetes`, `k8s`, `jenkins`, `github\s+actions`, `gitlab[\s-]ci`, `amazon\s+web\s+services`, `aws`, `azure`, `google\s+cloud`, `gcp`, `terraform`, `ansible` |
| TOOLS | `git(?:hub)?`, `ms\s+excel`, `(?-i:Excel)`, `power\s?bi`, `tableau`, `statistics` |

Example of the language of one fragment: `react(?:\.js|js)?` accepts exactly
{react, react.js, reactjs} (in any letter case).

### Design decisions

* **Case-sensitive fragments for ambiguous words.** `R`, `Shell`, `Express`,
  `Excel`, `REST` are English words or a single letter. Only the capitalised
  form is accepted, so "the rest of the team" or "excel at teamwork" are not
  qualifications (`tests/test_extraction.py::test_common_words_are_not_skills`).
* **Leftmost-longest resolution.** All category patterns run over the text;
  when two matches overlap the longest is kept: `Py Torch` (ML_DATA) beats
  `Py` (LANGUAGES), `GitHub Actions` beats `GitHub`.
* **Masking.** E-mails and profile URLs are replaced by blanks before skills are
  searched, so `github.com/pparker` does not produce the skill `github`.
* **Consistency with Stage 2.** A test checks that every variant of the catalog
  is fully matched by its category pattern, so nothing extracted is lost later.

### Limitations

* Skills written with typos (`Pyhton`) or not in the catalog are not found.
* Context is not analysed: "I don't know Java" still extracts `Java`.
* A degree field containing a skill word (`Applied Statistics`) is also counted
  as that skill.
