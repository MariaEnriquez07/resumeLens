# Stage 4 — Candidate Profile Language (RCPL) with a context-free grammar

Implementation: grammar `resumelens/dsl/resume.tx` (textX), serializer and
validation `resumelens/dsl/__init__.py`, visualization `resumelens/render.py`.

The DSL describes the **structured result** of ResumeLens: personal and
contact information, education, experience, normalized skills and the
classification result for every profile. Files use the extension `.resume`.

## Example

```
resume {
    candidate "Wednesday Addams";

    contact {
    }

    experience {
        total years: 3;
        summary: "developing web applications";
    }

    skills {
        LANGUAGES: JAVASCRIPT;
        FRAMEWORKS: REACT, NODE_JS;
        DATABASES: POSTGRESQL;
        TOOLS: GIT;
    }

    classification {
        profile FULL_STACK_DEVELOPER is ACCEPTED via DFA
            sequence: JAVASCRIPT, REACT, NODE_JS, POSTGRESQL, GIT;
        profile MACHINE_LEARNING_ENGINEER is REJECTED via NFA
            sequence: POSTGRESQL, GIT
            missing: "Python", "Pandas or NumPy", "Scikit-learn, TensorFlow or PyTorch";
        ...
    }
}
```

## Grammar in EBNF

Notation: `{ x }` zero or more, `[ x ]` optional, `|` alternative, terminals in
quotes or as UPPER-CASE lexical classes.

```ebnf
Resume          = "resume" "{" Candidate Contact [ EducationSection ]
                  [ ExperienceSection ] SkillsSection ClassificationSection "}" ;
Candidate       = "candidate" STRING ";" ;

Contact         = "contact" "{" { ContactItem } "}" ;
ContactItem     = EmailItem | PhoneItem | LinkItem ;
EmailItem       = "email" ":" EMAIL ";" ;
PhoneItem       = "phone" ":" PHONE ";" ;
LinkItem        = LinkKind ":" URL ";" ;
LinkKind        = "linkedin" | "github" | "website" ;

EducationSection = "education" "{" Degree { Degree } "}" ;
Degree          = "degree" DegreeLevel STRING [ "at" STRING ] [ "year" YEAR ] ";" ;
DegreeLevel     = "TECHNICIAN" | "TECHNOLOGIST" | "BACHELOR" | "MASTER" | "PHD" ;

ExperienceSection = "experience" "{" [ "total" "years" ":" INT ";" ]
                    [ "summary" ":" STRING ";" ] { Job } "}" ;
Job             = "job" STRING "at" STRING "from" YEAR "to" JobEnd ";" ;
JobEnd          = YEAR | "PRESENT" ;

SkillsSection   = "skills" "{" { SkillGroup } "}" ;
SkillGroup      = Category ":" SKILL { "," SKILL } ";" ;
Category        = "LANGUAGES" | "FRAMEWORKS" | "DATABASES" | "ML_DATA"
                | "DEVOPS_CLOUD" | "TOOLS" ;

ClassificationSection = "classification" "{" ProfileResult { ProfileResult } "}" ;
ProfileResult   = "profile" ProfileName "is" Status "via" AutomatonKind
                  [ "sequence" ":" SKILL { "," SKILL } ]
                  [ "missing" ":" STRING { "," STRING } ] ";" ;
ProfileName     = "FULL_STACK_DEVELOPER" | "MACHINE_LEARNING_ENGINEER"
                | "DEVOPS_ENGINEER" | "DATA_ANALYST" ;
Status          = "ACCEPTED" | "REJECTED" ;
AutomatonKind   = "DFA" | "NFA" | "ENFA" ;

(* lexical rules *)
SKILL  = UPPER { UPPER | DIGIT | "_" } ;                          (* /[A-Z][A-Z0-9_]*/ *)
EMAIL  = LOCAL "@" LABEL "." LABEL { "." LABEL } ;               (* /[A-Za-z0-9._%+-]+@…/ *)
PHONE  = [ "+" ] ( DIGIT | "(" ) { DIGIT | " " | "(" | ")" | "-" } DIGIT ;
URL    = ( "http://" | "https://" ) NONBLANK { NONBLANK } ;
YEAR   = ( "19" | "20" ) DIGIT DIGIT ;
STRING = '"' { CHARACTER } '"' ;                                 (* textX built-in *)
INT    = DIGIT { DIGIT } ;                                       (* textX built-in *)
```

## Terminals and non-terminals

**Non-terminals (22):** Resume, Candidate, Contact, ContactItem, EmailItem,
PhoneItem, LinkItem, LinkKind, EducationSection, Degree, DegreeLevel,
ExperienceSection, Job, JobEnd, SkillsSection, SkillGroup, Category,
ClassificationSection, ProfileResult, ProfileName, Status, AutomatonKind.
(LinkKind, DegreeLevel, JobEnd, Category, ProfileName, Status and AutomatonKind
are *match rules* in textX: they produce a string instead of an object.)

**Terminals:**
* keywords and punctuation: `resume candidate contact email phone linkedin github
  website education degree at year experience total years summary job from to
  PRESENT skills classification profile is via sequence missing
  { } : ; ,` and the enumerated values of DegreeLevel, Category, ProfileName,
  Status and AutomatonKind;
* lexical classes (regular languages): SKILL, EMAIL, PHONE, URL, YEAR, STRING, INT.

Start symbol: **Resume**.

## Structural characteristics

* **Block structure.** Each section is delimited by `{ … }`; blocks nest one
  level (Resume → section → items). Matching braces is the typical
  non-regular feature that requires a context-free grammar.
* **Fixed order of sections** (candidate, contact, education, experience,
  skills, classification), which makes documents easy to compare.
* **Optional sections**: education and experience (`?` in textX).
* **Repeated elements**: several degrees, several jobs, several skill groups,
  several contact items, one result per profile (`*=` / `+=` in textX), and
  comma-separated lists of skills and missing requirements (`+=X[',']`).
* **Statements end with `;`**, which gives the parser a clear
  synchronisation point and precise error positions.
* **Closed vocabularies**: categories, profile names, statuses and automaton
  kinds are enumerated in the grammar, so an unknown profile is a syntax error.
* **Lexical layer**: SKILL only accepts canonical upper-case tokens, so a
  non-normalized skill (`javascript`) is rejected — the DSL can only contain the
  output of Stage 2.

## Validation

**Lexical and syntactic** errors are detected by the parser generated by textX
(`TextXSyntaxError`, with line and column).

**Semantic (context-sensitive) rules** are object processors registered on the
metamodel (`TextXSemanticError`). They cannot be expressed by a context-free
grammar:

| Rule | Processor |
|---|---|
| A skill belongs to the category of its group | `_check_skill_group` |
| No duplicated skill inside a group | `_check_skill_group` |
| One result per profile; ACCEPTED needs a sequence and no missing items | `_check_classification` |

Test files: `samples/invalid/*.resume` (5 lexical/syntactic + 3 semantic),
`samples/valid_*.resume`.

```
$ python -m resumelens validate samples/invalid/lexical_bad_email.resume
REJECTED (syntax error) 3:22: Expected EMAIL
$ python -m resumelens validate samples/invalid/semantic_wrong_category.resume
REJECTED (semantic error) 7:9: Skill 'REACT' belongs to FRAMEWORKS, not DATABASES
```

## Visualization

`render.to_html(model)` reads **only the validated textX model**, so every page corresponds to a specification accepted
by the grammar. The HTML shows each accepted profile as the path of symbols the
automaton read (ending in a double circle), the missing requirements of the
rejected profiles, the normalized skills by category, education and experience.
