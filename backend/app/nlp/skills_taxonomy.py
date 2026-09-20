"""Skill taxonomy used for keyword / skill extraction.

Each canonical skill belongs to one category and carries a list of surface
forms (aliases). Matching is done on the *normalised* text with word-boundary
regexes so that "C++" or "scikit-learn" survive tokenisation, and so that
"R" does not match every stray letter.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

CATEGORIES = [
    "Machine Learning",
    "Deep Learning",
    "NLP",
    "SQL/Data",
    "Programming",
    "Tools",
]


@dataclass(frozen=True)
class Skill:
    name: str
    category: str
    aliases: tuple[str, ...]


def _s(name: str, category: str, *aliases: str) -> Skill:
    return Skill(name=name, category=category, aliases=(name.lower(),) + tuple(a.lower() for a in aliases))


SKILLS: tuple[Skill, ...] = (
    # --- Machine Learning -------------------------------------------------
    _s("Machine Learning", "Machine Learning", "ml", "machine-learning", "statistical learning"),
    _s("Regression", "Machine Learning", "linear regression", "logistic regression", "regression models"),
    _s("Classification", "Machine Learning", "classifier", "classification models"),
    _s("Clustering", "Machine Learning", "k-means", "kmeans", "unsupervised learning"),
    _s("Feature Engineering", "Machine Learning", "feature extraction", "feature selection"),
    _s("Model Evaluation", "Machine Learning", "cross validation", "cross-validation", "roc auc", "a/b testing", "model validation"),
    _s("Ensemble Methods", "Machine Learning", "random forest", "gradient boosting", "xgboost", "lightgbm", "boosting"),
    _s("Recommendation Systems", "Machine Learning", "recommender", "recommendation engine", "collaborative filtering"),
    _s("MLOps", "Machine Learning", "ml ops", "model deployment", "model monitoring", "mlflow"),
    # --- Deep Learning ----------------------------------------------------
    _s("Deep Learning", "Deep Learning", "dl", "deep neural"),
    _s("Neural Networks", "Deep Learning", "neural network", "ann", "mlp", "perceptron"),
    _s("CNN", "Deep Learning", "convolutional neural network", "convolutional", "computer vision", "cnns"),
    _s("RNN/LSTM", "Deep Learning", "rnn", "lstm", "gru", "recurrent neural network", "sequence models"),
    _s("Transformers", "Deep Learning", "transformer", "attention mechanism", "bert", "gpt", "llm", "large language model"),
    _s("Generative AI", "Deep Learning", "genai", "gen ai", "diffusion model", "rag", "retrieval augmented generation"),
    # --- NLP --------------------------------------------------------------
    _s("Natural Language Processing", "NLP", "nlp", "natural language"),
    _s("Text Preprocessing", "NLP", "tokenization", "tokenisation", "lemmatization", "stemming", "stop words", "text cleaning"),
    _s("TF-IDF", "NLP", "tf idf", "tfidf", "bag of words", "bag-of-words"),
    _s("Word2Vec", "NLP", "word2vec", "glove", "fasttext"),
    _s("Embeddings", "NLP", "embedding", "vector search", "sentence embeddings", "vector database"),
    _s("Sentiment Analysis", "NLP", "sentiment", "opinion mining"),
    _s("Named Entity Recognition", "NLP", "ner", "entity extraction"),
    _s("spaCy", "NLP", "spacy"),
    _s("NLTK", "NLP", "nltk"),
    # --- SQL / Data -------------------------------------------------------
    _s("SQL", "SQL/Data", "sql", "t-sql", "pl/sql", "ansi sql"),
    _s("Joins", "SQL/Data", "join", "inner join", "left join"),
    _s("CTEs", "SQL/Data", "cte", "common table expression", "common table expressions"),
    _s("Window Functions", "SQL/Data", "window function", "analytic functions", "rank() over", "partition by"),
    _s("Database Design", "SQL/Data", "database concepts", "normalization", "schema design", "indexing", "dbms", "er diagram"),
    _s("PostgreSQL", "SQL/Data", "postgres", "psql"),
    _s("NoSQL", "SQL/Data", "mongodb", "cassandra", "dynamodb", "redis"),
    _s("Data Warehousing", "SQL/Data", "data warehouse", "snowflake", "bigquery", "redshift", "dbt"),
    _s("ETL/Data Pipelines", "SQL/Data", "etl", "elt", "data pipeline", "airflow", "spark", "pyspark", "kafka"),
    _s("Pandas", "SQL/Data", "pandas", "numpy", "dataframe"),
    _s("Statistics", "SQL/Data", "statistical", "probability", "hypothesis testing", "statistics"),
    # --- Programming ------------------------------------------------------
    _s("Python", "Programming", "python3", "python 3"),
    _s("Java", "Programming", "java 8", "java8", "core java"),
    _s("C++", "Programming", "c\\+\\+", "cpp"),
    _s("JavaScript", "Programming", "javascript", "typescript", "node.js", "nodejs", "react"),
    _s("Data Structures & Algorithms", "Programming", "dsa", "data structures", "algorithms", "problem solving", "competitive programming"),
    _s("Object Oriented Programming", "Programming", "oop", "object-oriented", "object oriented design"),
    _s("System Design", "Programming", "distributed systems", "scalable systems", "low level design", "high level design"),
    _s("R", "Programming", "\\br programming\\b", "\\bin r\\b"),
    _s("Scala", "Programming", "scala"),
    _s("Go", "Programming", "golang"),
    # --- Tools ------------------------------------------------------------
    _s("Git/GitHub", "Tools", "git", "github", "gitlab", "version control"),
    _s("Docker", "Tools", "docker", "container", "kubernetes", "k8s"),
    _s("Cloud", "Tools", "aws", "azure", "gcp", "google cloud", "cloud platform", "sagemaker"),
    _s("Streamlit", "Tools", "streamlit", "gradio"),
    _s("Power BI/Tableau", "Tools", "power bi", "powerbi", "tableau", "looker", "data visualization", "dashboarding"),
    _s("TensorFlow/PyTorch", "Tools", "tensorflow", "pytorch", "keras", "torch"),
    _s("scikit-learn", "Tools", "scikit learn", "sklearn", "scikit-learn"),
    _s("Linux", "Tools", "unix", "shell scripting", "bash"),
    _s("REST APIs", "Tools", "rest api", "fastapi", "flask", "django", "microservices"),
    _s("CI/CD", "Tools", "ci/cd", "jenkins", "github actions", "continuous integration"),
)

SKILLS_BY_NAME: dict[str, Skill] = {skill.name.lower(): skill for skill in SKILLS}

# Pre-compiled alias patterns. Aliases that already contain regex escapes
# (e.g. "c\+\+") are used as-is, everything else is escaped.
def _compile(alias: str) -> re.Pattern[str]:
    pattern = alias if "\\" in alias else re.escape(alias)
    return re.compile(rf"(?<![\w+#]){pattern}(?![\w+#])", re.IGNORECASE)


_ALIAS_PATTERNS: list[tuple[Skill, re.Pattern[str]]] = [
    (skill, _compile(alias)) for skill in SKILLS for alias in skill.aliases
]


def extract_skills(text: str) -> dict[str, int]:
    """Return {canonical skill name: number of alias matches} found in `text`."""
    if not text:
        return {}
    counts: dict[str, int] = {}
    for skill, pattern in _ALIAS_PATTERNS:
        hits = len(pattern.findall(text))
        if hits:
            counts[skill.name] = counts.get(skill.name, 0) + hits
    return counts


def normalise_user_skill(raw: str) -> str | None:
    """Map a free-text user skill onto a canonical taxonomy skill name."""
    token = raw.strip().lower()
    if not token:
        return None
    if token in SKILLS_BY_NAME:
        return SKILLS_BY_NAME[token].name
    for skill in SKILLS:
        for alias in skill.aliases:
            plain = alias.replace("\\", "")
            if token == plain:
                return skill.name
    # Fall back to alias containment (e.g. "ml engineering" -> Machine Learning).
    for skill, pattern in _ALIAS_PATTERNS:
        if pattern.search(token):
            return skill.name
    return None


def category_of(skill_name: str) -> str | None:
    skill = SKILLS_BY_NAME.get(skill_name.lower())
    return skill.category if skill else None
