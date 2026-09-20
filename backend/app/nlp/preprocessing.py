"""Text preprocessing for job descriptions.

The pipeline is intentionally dependency-tolerant: spaCy gives the best
lemmatisation, NLTK is the fallback, and a pure-Python tokeniser is used when
neither model is installed. This keeps the API functional in constrained
environments (CI, small containers) without silently changing behaviour - the
active backend is reported by `active_backend()` and surfaced in /api/health.
"""
from __future__ import annotations

import re
from functools import lru_cache

# Domain stopwords: extremely common recruitment boilerplate that carries no
# signal about the technical requirements of a role.
EXTRA_STOPWORDS = {
    "job", "role", "work", "working", "team", "teams", "company", "candidate", "candidates",
    "intern", "internship", "opportunity", "opportunities", "experience", "experiences",
    "year", "years", "strong", "good", "excellent", "ability", "skill", "skills",
    "responsibility", "responsibilities", "requirement", "requirements", "prefer",
    "preferred", "plus", "etc", "u", "us", "will", "must", "should", "using", "use",
}

_BASE_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "have", "he",
    "in", "is", "it", "its", "of", "on", "or", "that", "the", "to", "was", "were", "will",
    "with", "you", "your", "our", "we", "they", "this", "these", "those", "their", "who",
    "which", "what", "when", "where", "how", "all", "any", "both", "each", "more", "most",
    "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than",
    "too", "very", "can", "just", "also", "into", "about", "across", "over", "up", "out",
}

_TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9+#./_-]*")
_WHITESPACE_RE = re.compile(r"\s+")

_backend = "regex"
_nlp = None
_lemmatizer = None
_stopwords: set[str] = set(_BASE_STOPWORDS) | EXTRA_STOPWORDS


def _init_backend() -> None:
    """Pick the best available NLP backend exactly once."""
    global _backend, _nlp, _lemmatizer, _stopwords
    try:  # pragma: no cover - depends on optional model download
        import spacy

        _nlp = spacy.load("en_core_web_sm", disable=["parser", "ner"])
        _stopwords = set(_nlp.Defaults.stop_words) | EXTRA_STOPWORDS
        _backend = "spacy"
        return
    except Exception:
        _nlp = None
    try:  # pragma: no cover - depends on optional nltk data
        from nltk.corpus import stopwords as nltk_stopwords
        from nltk.stem import WordNetLemmatizer

        _stopwords = set(nltk_stopwords.words("english")) | EXTRA_STOPWORDS
        _lemmatizer = WordNetLemmatizer()
        _lemmatizer.lemmatize("testing")  # force wordnet load, raises if missing
        _backend = "nltk"
        return
    except Exception:
        _lemmatizer = None
    _backend = "regex"


_init_backend()


def active_backend() -> str:
    """Name of the tokenisation/lemmatisation backend actually in use."""
    return _backend


def clean_text(text: str) -> str:
    """Lowercase, strip URLs/markup and collapse whitespace."""
    text = text.lower()
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("\u2019", "'")
    return _WHITESPACE_RE.sub(" ", text).strip()


@lru_cache(maxsize=2048)
def tokenize(text: str) -> tuple[str, ...]:
    """Clean -> tokenise -> lemmatise -> drop stopwords and 1-char tokens."""
    cleaned = clean_text(text)
    if _backend == "spacy" and _nlp is not None:  # pragma: no cover - optional
        tokens = [t.lemma_.lower() for t in _nlp(cleaned) if not t.is_space and not t.is_punct]
    else:
        tokens = _TOKEN_RE.findall(cleaned)
        if _backend == "nltk" and _lemmatizer is not None:  # pragma: no cover - optional
            tokens = [_lemmatizer.lemmatize(t) for t in tokens]
    keep = []
    for token in tokens:
        token = token.strip(".-_/")
        if len(token) < 2 and token not in {"c", "r"}:
            continue
        if token in _stopwords:
            continue
        keep.append(token)
    return tuple(keep)


def preprocess(text: str) -> str:
    """Return the preprocessed document as a space separated string."""
    return " ".join(tokenize(text))
