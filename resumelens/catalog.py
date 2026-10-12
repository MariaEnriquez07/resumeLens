"""Qualification catalog shared by every stage.

The catalog is the single source of truth for:

* the **categories** of qualifications (one finite-state transducer per category),
* the **canonical tokens** (output alphabet Γ of the transducers and input
  alphabet Σ of the recognition automata),
* the **surface variants** that each transducer maps to a canonical token.

Variants are written in lower case. Case is handled *inside* the transducers
(each letter transition exists for its upper- and lower-case form), so the
transducers themselves model case-insensitivity.
"""

from __future__ import annotations

# Order of categories = global canonical order used when listing skills.
CATEGORIES: tuple[str, ...] = (
    "LANGUAGES",
    "FRAMEWORKS",
    "DATABASES",
    "ML_DATA",
    "DEVOPS_CLOUD",
    "TOOLS",
)

CATEGORY_TITLES: dict[str, str] = {
    "LANGUAGES": "Programming languages",
    "FRAMEWORKS": "Frameworks, libraries and APIs",
    "DATABASES": "Databases",
    "ML_DATA": "Machine learning and data",
    "DEVOPS_CLOUD": "DevOps and cloud",
    "TOOLS": "Tools and analytics",
}

# category -> canonical token -> surface variants (lower case)
# Kept small on purpose: 1–3 variants per qualification, enough to show the
# normalization problem without making the transducers hard to read.
LEXICON: dict[str, dict[str, tuple[str, ...]]] = {
    "LANGUAGES": {
        "JAVASCRIPT": ("javascript", "js"),
        "TYPESCRIPT": ("typescript", "ts"),
        "PYTHON": ("python", "py"),
        "BASH": ("bash", "shell"),
        "R": ("r",),
    },
    "FRAMEWORKS": {
        "REACT": ("react", "react.js", "reactjs"),
        "ANGULAR": ("angular", "angularjs"),
        "VUE": ("vue", "vue.js"),
        "NODE_JS": ("node.js", "nodejs", "node"),
        "EXPRESS": ("express", "express.js"),
        "DJANGO": ("django",),
        "SPRING_BOOT": ("spring boot", "springboot"),
        "REST_API": ("rest api", "rest apis", "rest"),
    },
    "DATABASES": {
        "SQL": ("sql",),
        "NOSQL": ("nosql", "no-sql"),
        "POSTGRESQL": ("postgresql", "postgres"),
        "MYSQL": ("mysql",),
        "MONGODB": ("mongodb", "mongo"),
        "SQLITE": ("sqlite",),
    },
    "ML_DATA": {
        "PANDAS": ("pandas",),
        "NUMPY": ("numpy",),
        "SCIKIT_LEARN": ("scikit-learn", "scikit learn", "sklearn"),
        "TENSORFLOW": ("tensorflow", "tensor flow"),
        "PYTORCH": ("pytorch", "py torch"),
        "ML_MODELING": ("machine learning", "predictive models"),
    },
    "DEVOPS_CLOUD": {
        "LINUX": ("linux", "ubuntu"),
        "DOCKER": ("docker",),
        "KUBERNETES": ("kubernetes", "k8s"),
        "JENKINS": ("jenkins",),
        "GITHUB_ACTIONS": ("github actions",),
        "GITLAB_CI": ("gitlab ci", "gitlab-ci"),
        "AWS": ("aws", "amazon web services"),
        "AZURE": ("azure",),
        "GCP": ("gcp", "google cloud"),
        "TERRAFORM": ("terraform",),
        "ANSIBLE": ("ansible",),
    },
    "TOOLS": {
        "GIT": ("git", "github"),
        "EXCEL": ("excel", "ms excel"),
        "POWER_BI": ("power bi", "powerbi"),
        "TABLEAU": ("tableau",),
        "STATISTICS": ("statistics",),
    },
}


def token_category(token: str) -> str | None:
    """Return the category a canonical token belongs to (or None)."""
    for category, entries in LEXICON.items():
        if token in entries:
            return category
    return None


def all_tokens() -> list[str]:
    """All canonical tokens in global canonical order."""
    return [tok for cat in CATEGORIES for tok in LEXICON[cat]]


def global_order_key(token: str) -> int:
    order = all_tokens()
    return order.index(token) if token in order else len(order)
