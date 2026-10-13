"""Professional profiles.

A profile is an ordered list of *slots*. Each slot is a requirement that is
satisfied by one or more canonical tokens from a set of alternatives, e.g.
``Slot("data_processing", ("PANDAS", "NUMPY"))`` means "Pandas or NumPy".

The order of the slots is the **canonical order** of the profile: before a
résumé reaches the automaton, its tokens are filtered to the profile alphabet
and sorted by slot (and, inside a slot, by the order of the alternatives).

The language recognised for a profile with slots S1..Sn is

    L = X1 X2 ... Xn      where Xi = Ai+   if Si is required
                                Xi = Ai*   if Si is optional
                                (Ai = alternatives of Si)

``construction`` is the type of automaton that models the profile
(DFA, NFA or ENFA for ε-NFA).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Slot:
    name: str
    alternatives: tuple[str, ...]
    optional: bool = False
    description: str = ""


@dataclass(frozen=True)
class Profile:
    key: str
    title: str
    area: str
    construction: str  # "DFA" | "NFA" | "ENFA"
    slots: tuple[Slot, ...]
    summary: str = ""

    @property
    def alphabet(self) -> list[str]:
        return [tok for slot in self.slots for tok in slot.alternatives]

    def slot_of(self, token: str) -> int | None:
        for i, slot in enumerate(self.slots):
            if token in slot.alternatives:
                return i
        return None

    def order_key(self, token: str) -> tuple[int, int]:
        i = self.slot_of(token)
        assert i is not None
        return (i, self.slots[i].alternatives.index(token))

    def canonical_sequence(self, tokens: list[str]) -> list[str]:
        """Filter tokens to the profile alphabet and sort them canonically."""
        unique = list(dict.fromkeys(tokens))
        kept = [t for t in unique if self.slot_of(t) is not None]
        return sorted(kept, key=self.order_key)

    def missing_requirements(self, tokens: list[str]) -> list[Slot]:
        present = set(tokens)
        return [s for s in self.slots
                if not s.optional and not present.intersection(s.alternatives)]


FULL_STACK = Profile(
    key="FULL_STACK_DEVELOPER",
    title="Full Stack Developer",
    area="Software engineering",
    construction="DFA",
    summary="Builds client-side and server-side components: a frontend "
            "language and framework, a backend technology, a database and "
            "version control. REST API experience is valued but optional.",
    slots=(
        Slot("frontend_language", ("JAVASCRIPT", "TYPESCRIPT"),
             description="JavaScript or TypeScript"),
        Slot("frontend_framework", ("REACT", "ANGULAR", "VUE"),
             description="React, Angular or Vue"),
        Slot("backend", ("NODE_JS", "EXPRESS", "DJANGO", "SPRING_BOOT"),
             description="Node.js, Express, Django or Spring Boot"),
        Slot("api", ("REST_API",), optional=True,
             description="REST APIs (optional)"),
        Slot("database", ("SQL", "NOSQL", "POSTGRESQL", "MYSQL", "MONGODB", "SQLITE"),
             description="SQL or NoSQL database"),
        Slot("version_control", ("GIT",), description="Git"),
    ),
)

ML_ENGINEER = Profile(
    key="MACHINE_LEARNING_ENGINEER",
    title="Machine Learning Engineer",
    area="AI / data",
    construction="NFA",
    summary="Builds learning-based systems: Python, data processing, at least "
            "one ML framework, SQL and Git. Explicit model-development "
            "experience is optional.",
    slots=(
        Slot("language", ("PYTHON",), description="Python"),
        Slot("data_processing", ("PANDAS", "NUMPY"), description="Pandas or NumPy"),
        Slot("ml_framework", ("SCIKIT_LEARN", "TENSORFLOW", "PYTORCH"),
             description="Scikit-learn, TensorFlow or PyTorch"),
        Slot("ml_modeling", ("ML_MODELING",), optional=True,
             description="Machine-learning model development (optional)"),
        Slot("database", ("SQL", "POSTGRESQL", "MYSQL"), description="SQL database"),
        Slot("version_control", ("GIT",), description="Git"),
    ),
)

DEVOPS = Profile(
    key="DEVOPS_ENGINEER",
    title="DevOps Engineer",
    area="Software engineering",
    construction="ENFA",
    summary="Automates building, deployment and operation of software: Linux, "
            "scripting, containers, orchestration, CI/CD, a cloud provider and "
            "Git. Infrastructure as code is optional.",
    slots=(
        Slot("operating_system", ("LINUX",), description="Linux"),
        Slot("scripting", ("BASH", "PYTHON"), description="Bash or Python"),
        Slot("containers", ("DOCKER",), description="Docker"),
        Slot("orchestration", ("KUBERNETES",), description="Kubernetes"),
        Slot("ci_cd", ("JENKINS", "GITHUB_ACTIONS", "GITLAB_CI"),
             description="Jenkins, GitHub Actions or GitLab CI"),
        Slot("cloud", ("AWS", "AZURE", "GCP"), description="AWS, Azure or GCP"),
        Slot("infrastructure_as_code", ("TERRAFORM", "ANSIBLE"), optional=True,
             description="Terraform or Ansible (optional)"),
        Slot("version_control", ("GIT",), description="Git"),
    ),
)

DATA_ANALYST = Profile(
    key="DATA_ANALYST",
    title="Data Analyst",
    area="AI / data",
    construction="DFA",
    summary="Turns data into decisions: SQL querying, spreadsheets, a BI "
            "visualisation tool and Python or R. Statistics is optional.",
    slots=(
        Slot("querying", ("SQL", "MYSQL", "POSTGRESQL"), description="SQL"),
        Slot("spreadsheets", ("EXCEL",), description="Excel"),
        Slot("visualization", ("POWER_BI", "TABLEAU"), description="Power BI or Tableau"),
        Slot("programming", ("PYTHON", "R"), description="Python or R"),
        Slot("statistics", ("STATISTICS",), optional=True,
             description="Statistics (optional)"),
    ),
)

PROFILES: dict[str, Profile] = {
    p.key: p for p in (FULL_STACK, ML_ENGINEER, DEVOPS, DATA_ANALYST)
}
