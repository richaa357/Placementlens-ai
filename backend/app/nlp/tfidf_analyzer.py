"""TF-IDF analysis of job descriptions.

We fit a TF-IDF model over the job descriptions of a single company (plus, when
available, the wider corpus for a sane IDF) and use it for three things:

1. keyword extraction  - highest mean TF-IDF weight terms per company;
2. document similarity - cosine similarity between a user's skill profile and
   each job description;
3. role clustering     - grouping near-duplicate postings into role families.

Everything here is deterministic, which matters because the output is shown to
users as "analysis" and must be reproducible.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.nlp.preprocessing import preprocess


@dataclass
class Keyword:
    term: str
    weight: float


class TfidfAnalyzer:
    """Thin, well-behaved wrapper around scikit-learn's TfidfVectorizer."""

    def __init__(self, documents: list[str], ngram_range: tuple[int, int] = (1, 2)) -> None:
        self.raw_documents = documents
        self.documents = [preprocess(doc) for doc in documents]
        self._fitted = False
        self.matrix = None
        # min_df=1 because a company usually has only a handful of postings;
        # sublinear_tf dampens the effect of a term repeated in one long JD.
        self.vectorizer = TfidfVectorizer(
            ngram_range=ngram_range,
            min_df=1,
            max_df=0.95 if len(self.documents) > 4 else 1.0,
            sublinear_tf=True,
            token_pattern=r"(?u)\b[\w+#./-]{2,}\b",
        )
        non_empty = [doc for doc in self.documents if doc.strip()]
        if non_empty:
            try:
                self.matrix = self.vectorizer.fit_transform(self.documents)
                self._fitted = True
            except ValueError:
                # Happens when every token is filtered out by max_df/min_df.
                self._fitted = False

    @property
    def is_fitted(self) -> bool:
        return self._fitted

    def top_keywords(self, top_n: int = 25) -> list[Keyword]:
        """Terms with the highest mean TF-IDF weight across the corpus."""
        if not self._fitted or self.matrix is None:
            return []
        mean_weights = np.asarray(self.matrix.mean(axis=0)).ravel()
        terms = self.vectorizer.get_feature_names_out()
        order = np.argsort(mean_weights)[::-1][:top_n]
        return [Keyword(term=str(terms[i]), weight=round(float(mean_weights[i]), 4)) for i in order if mean_weights[i] > 0]

    def similarity_to(self, query: str) -> list[float]:
        """Cosine similarity of `query` against every document (0..1)."""
        if not self._fitted or self.matrix is None:
            return [0.0] * len(self.documents)
        processed = preprocess(query)
        if not processed.strip():
            return [0.0] * len(self.documents)
        vector = self.vectorizer.transform([processed])
        if vector.nnz == 0:
            return [0.0] * len(self.documents)
        scores = cosine_similarity(vector, self.matrix).ravel()
        return [round(float(max(0.0, s)), 4) for s in scores]

    def pairwise_similarity(self) -> list[list[float]]:
        if not self._fitted or self.matrix is None:
            return []
        return np.round(cosine_similarity(self.matrix), 4).tolist()
