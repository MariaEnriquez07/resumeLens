# Stage 1 — Information extraction with regular expressions

Implementation: `resumelens/extraction.py` (Python `re`). Output:
`ExtractionResult`, saved as `<name>.extraction.json`.

This stage **only finds** strings. It keeps them exactly as written
(`Py Torch` stays `Py Torch`); deciding that two strings mean the same is the
job of Stage 2.

Notation used below: `\d` = a digit, `\w` = a letter, digit or `_`,
`\b` = word boundary (the position between a word character and a non-word
character), `?` = optional, `+` = one or more, `{m,n}` = between m and n times,
`(?:…)` = group without capture, `(…)` = captured group.

## 1. Contact information

### E-mail
```
[\w.+-]+@[\w-]+(?:\.[\w-]+)+
```
Language: a user part (letters, digits, `.`, `+`, `-`), the symbol `@`, a
domain, and **one or more** `.something` parts.
Accepts `peter.parker@dailybugle.com`, `a.b+cv@uni.edu.co`.
Rejects `test.example.com` (no `@`), `user@` and `@domain.com`.

### Phone
```
(?:\+\d{1,3} )?(?:\(\d{3}\)|\d{3})[ -]\d{3}[ -]\d{4}
```
Language: an optional country code (`+` and 1–3 digits, then a space), an area
code of 3 digits with or without parentheses, then 3 digits and 4 digits,
separated by a space or a hyphen.
Accepts `+57 300 123 4567`, `(602) 555-0199`, `+1 212 555 0147`.
Rejects `2019 - 2022` and `3 years`.

### LinkedIn and GitHub
```
linkedin\.com/in/[\w-]+
github\.com/[\w-]+
```
The fixed domain followed by a user name. Accepts `linkedin.com/in/peter-parker`
and `github.com/pparker`.

### Name
```
^([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?: [A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,3})$
```
Applied to the **first line** of the résumé: 2 to 4 words, each one a capital
letter followed by lower-case letters. Accepts `Mary Jane Watson`.

## 2. Professional experience

### Years of experience
```
(\d+)\+? (?:years?|yrs?) of experience ?([^.\n]*)
```
(case-insensitive) Language: a number, an optional `+`, the word `year`,
`years`, `yr` or `yrs`, the words `of experience`, and then the rest of the
sentence (any character except `.` and line break).
`3 years of experience developing web applications.` → years = 3,
summary = `developing web applications`.

### Jobs
```
^-? ?(.+?) at (.+?) \((\d{4}) - (\d{4}|Present)\)
```
(one match per line) Language: an optional bullet `-`, a role, the word `at`, a
company and a period `(YYYY - YYYY)` or `(YYYY - Present)`.
`.+?` is *lazy*: it takes as few characters as possible, so the role stops at
the first ` at `.
`DevOps Engineer at Oscorp Industries (2022 - Present)` →
role = `DevOps Engineer`, company = `Oscorp Industries`, 2022, `Present`.

## 3. Academic qualifications
```
^(Ph\.D\.|M\.Sc\.|B\.Sc\.|Master of Science|Bachelor of Science) in (.+?), (.+?) \((\d{4})\)$
```
(one match per line) Language: a degree level from a closed list, the word `in`,
the field, a comma, the institution and the year in parentheses.
`B.Sc. in Systems Engineering, Universidad Icesi (2020)` →
`B.Sc.`, `Systems Engineering`, `Universidad Icesi`, 2020.
Note: `\.` is a literal dot (a plain `.` means "any character").

## 4. Qualifications (one regular expression per category)

Each category is a list of alternatives separated by `|`, surrounded by `\b`
so a skill is not found inside another word (`py` is not found in `happy`).
Matching is case-insensitive except where `(?-i:…)` is written.

| Category | Regular expression (inside `\b(?: … )\b`) |
|---|---|
| ML_DATA | `scikit[ -]learn \| sklearn \| tensor ?flow \| py ?torch \| pandas \| numpy \| machine learning \| predictive models` |
| DEVOPS_CLOUD | `github actions \| gitlab[ -]ci \| amazon web services \| google cloud \| kubernetes \| k8s \| docker \| jenkins \| linux \| ubuntu \| aws \| azure \| gcp \| terraform \| ansible` |
| FRAMEWORKS | `react\.js \| reactjs \| react \| angularjs \| angular \| vue\.js \| vue \| node\.js \| nodejs \| node \| express\.js \| (?-i:Express) \| django \| spring ?boot \| rest apis? \| (?-i:REST)` |
| DATABASES | `postgresql \| postgres \| mysql \| mongodb \| mongo \| sqlite \| no-?sql \| sql` |
| LANGUAGES | `javascript \| js \| typescript \| ts \| python \| py \| bash \| (?-i:Shell) \| (?-i:R)` |
| TOOLS | `github \| git \| ms excel \| (?-i:Excel) \| power ?bi \| tableau \| statistics` |

Example of the language of one fragment: `react\.js|reactjs|react` accepts
exactly {react.js, reactjs, react}, in any letter case.

### How the six expressions are used together

The six are joined into one expression, each as a **named group**:

```
\b(?: (?P<ML_DATA>…) | (?P<DEVOPS_CLOUD>…) | (?P<FRAMEWORKS>…) | (?P<DATABASES>…) | (?P<LANGUAGES>…) | (?P<TOOLS>…) )\b
```

`finditer` scans the text from left to right; for each match, the name of the
group that matched is the category of the skill.

Python tries the alternatives **in the order they are written** and keeps the
first one that matches. Two simple rules follow from that:

1. **Longer alternatives first inside a category**: `node\.js` before `node`,
   `postgresql` before `sql`. Otherwise `Node.js` would be read as `Node`.
2. **Categories in a fixed order**: ML_DATA before LANGUAGES, so `Py Torch` is
   read as one skill (PyTorch) and not as `Py`; DEVOPS_CLOUD before TOOLS, so
   `GitHub Actions` is not read as `GitHub`.

### Other design decisions

* **Case-sensitive ambiguous words.** `R`, `Shell`, `Express`, `Excel` and
  `REST` are also common English words or a single letter. They are only
  accepted with that capitalisation, so "the rest of the team" or "excel at
  teamwork" are not qualifications.
* **E-mails and links are removed first.** Before searching for skills, the
  e-mails and profile links are replaced by blanks, so `github.com/pparker` is
  not read as the skill `github`.
* **Consistency with Stage 2.** A test checks that every variant of the catalog
  is matched by the regular expression of its category, so nothing extracted is
  lost in the next stage.

## Limitations

* Skills written with typos (`Pyhton`) or not in the catalog are not found.
* Context is not analysed: "I don't know Python" still extracts `Python`.
* Jobs and degrees must follow the formats above; other formats are not found.
* A degree field containing a skill word (`Applied Statistics`) is also counted
  as that skill.
