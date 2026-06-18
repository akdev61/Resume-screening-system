import io
import re
from pypdf import PdfReader


# ── PDF extraction ─────────────────────────────────────────────────────────────

def extract_text_from_pdf(content: bytes) -> str:
    """Extract text from PDF bytes using pypdf (maintained successor to PyPDF2)."""
    try:
        reader = PdfReader(io.BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception:
        return ""


# ── Stop words ─────────────────────────────────────────────────────────────────

_STOPWORDS = {
    "the","a","an","and","or","but","in","on","at","to","for","of","with","by",
    "from","is","are","was","were","be","been","have","has","had","do","does",
    "did","will","would","could","should","may","might","shall","can","this",
    "that","these","those","i","we","you","he","she","it","they","our","your",
    "their","my","his","her","its","as","if","not","no","so","up","out","about",
    "than","into","through","during","including","while","although","experience",
    "years","year","work","working","knowledge","ability","skills","skill",
    "strong","good","excellent","candidate","position","role","team","looking",
    "required","responsibilities","requirements","also","well","etc","use",
    "using","used","able","must","new","high","level","within","across","both",
    "each","such","more","other","than","then","when","where","which","who",
    "help","build","develop","create","manage","support","ensure","provide",
}


# ── Tech skill list (ported from old version, fixed matching) ──────────────────
# Uses plain substring `in` matching — no regex escape issues (fixes old c++ bug)

_TECH_SKILLS = [
    # Languages
    "python", "java", "javascript", "typescript", "golang", "rust", "ruby",
    "php", "swift", "kotlin", "scala", "r", "matlab", "bash", "shell",
    "c++", "c#", "perl", "elixir", "haskell",
    # Frontend
    "react", "angular", "vue", "svelte", "next.js", "nuxt", "tailwind",
    "html", "css", "sass", "webpack", "vite",
    # Backend / frameworks
    "fastapi", "django", "flask", "express", "spring", "rails", "laravel",
    "node.js", "nestjs", "gin", "fiber", "actix",
    # Databases
    "postgresql", "mysql", "mongodb", "redis", "elasticsearch", "cassandra",
    "sqlite", "dynamodb", "neo4j", "influxdb", "clickhouse",
    # Cloud & DevOps
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "ansible",
    "jenkins", "github actions", "gitlab ci", "circleci", "helm", "nginx",
    "linux", "unix",
    # Data / ML
    "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "keras",
    "xgboost", "lightgbm", "spark", "airflow", "dbt", "kafka",
    "matplotlib", "seaborn", "plotly",
    # ML concepts (multi-word — checked with `in`, not token matching)
    "machine learning", "deep learning", "natural language processing",
    "computer vision", "generative ai", "large language model",
    "neural network", "random forest", "decision tree", "gradient boosting",
    "transformer", "fine-tuning", "reinforcement learning",
    # APIs & architecture
    "rest api", "graphql", "grpc", "websocket", "microservices",
    "event driven", "message queue", "rabbitmq", "celery",
    # Practices
    "ci/cd", "continuous integration", "unit testing", "integration testing",
    "test driven", "agile", "scrum", "devops", "version control",
    "object oriented", "functional programming", "system design",
    # Tools
    "git", "github", "gitlab", "jira", "confluence", "postman",
    "jupyter", "vscode", "linux",
]

# Skills with only alphanumeric chars → safe for token-set lookup
# Skills with special chars (c++, c#, node.js, ci/cd …) → substring match
# Multi-word skills → substring match
_TOKEN_SKILLS  = [s for s in _TECH_SKILLS if " " not in s and re.match(r'^[a-z0-9]+$', s)]
_SUBSTR_SKILLS = [s for s in _TECH_SKILLS if " " in s or not re.match(r'^[a-z0-9]+$', s)]


# ── Tokeniser — improved over old version ──────────────────────────────────────
# Uses re.findall (from old version) instead of split() — catches word boundaries
# properly and handles punctuation like slashes in "ci/cd", dots in "node.js"

def _tokenize(text: str) -> set[str]:
    """
    Tokenise text into a set of meaningful words.
    Improvement over old version: re.findall catches boundary tokens better,
    and we filter short tokens (len > 2) to cut noise from possessives / initials.
    """
    text = text.lower()
    # Keep alphanumeric + dots/plusses so "c++", "node.js" survive as single tokens
    text = re.sub(r"[^a-z0-9\s\.\+\#\/]", " ", text)
    tokens = re.findall(r"\b\w[\w\.\+\#\/]*\w\b|\b\w\b", text)
    return {t for t in tokens if t not in _STOPWORDS and len(t) > 2}


def _extract_skills(text: str) -> list[str]:
    """
    Extract recognised tech skills from text.

    Three matching strategies, each chosen to avoid the old version's c++ regex bug:
    - Pure alpha-numeric single words (python, docker, aws): token-set lookup — fast, boundary-safe
    - Special-char skills (c++, c#, node.js, ci/cd): plain `in` substring — no regex escaping needed
    - Multi-word phrases (machine learning, rest api): plain `in` substring
    """
    text_lower = text.lower()
    tokens = _tokenize(text)
    found: list[str] = []

    # Pure alphanumeric single words — token set (boundary-safe, O(1) lookup)
    for skill in _TOKEN_SKILLS:
        if skill in tokens:
            found.append(skill)

    # Special-char + multi-word skills — substring match (no regex, no escape issues)
    for skill in _SUBSTR_SKILLS:
        if skill in text_lower:
            found.append(skill)

    return found


# ── Scoring ────────────────────────────────────────────────────────────────────

def score_resume_against_job(job_description: str, resume_text: str) -> tuple[float, str]:
    """
    Score a resume against a job description.

    Scoring breakdown:
      60% — token overlap ratio  (how many JD keywords appear in the resume)
      25% — skill match ratio    (how many JD skills the resume also has)
      15% — phrase bonus         (multi-word tech phrases matched in both)

    Returns (score_0_to_100, comma_separated_matched_keywords).
    """
    if not resume_text.strip():
        return 0.0, ""

    jd_tokens  = _tokenize(job_description)
    rv_tokens  = _tokenize(resume_text)

    if not jd_tokens:
        return 0.0, ""

    # ── Component 1: token overlap (improved from old version's single metric) ──
    common_tokens = jd_tokens & rv_tokens
    token_score   = len(common_tokens) / len(jd_tokens)  # 0.0–1.0

    # ── Component 2: skill match (new — not in old version) ───────────────────
    jd_skills  = set(_extract_skills(job_description))
    rv_skills  = set(_extract_skills(resume_text))
    matched_skills = jd_skills & rv_skills
    skill_score = (len(matched_skills) / len(jd_skills)) if jd_skills else 0.0

    # ── Component 3: multi-word phrase bonus (kept from old version logic) ─────
    jd_lower = job_description.lower()
    rv_lower = resume_text.lower()
    matched_phrases = [p for p in _SUBSTR_SKILLS if p in jd_lower and p in rv_lower]
    phrase_bonus = min(len(matched_phrases) * 0.03, 0.15)  # cap at 15%

    # ── Weighted final score ───────────────────────────────────────────────────
    raw = (token_score * 0.60) + (skill_score * 0.25) + phrase_bonus
    score = round(min(raw, 1.0) * 100, 1)

    # ── Keywords to surface in results UI ─────────────────────────────────────
    # Combine token matches + matched skills + matched phrases, deduplicated
    all_keywords = sorted(
        common_tokens
        | matched_skills
        | {p for p in matched_phrases}
    )
    keywords_str = ", ".join(all_keywords[:25])  # cap at 25 for readability

    return score, keywords_str
