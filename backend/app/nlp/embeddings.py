"""Semantic (embedding based) similarity.

Three backends, tried in order:

1. `sentence-transformers` (best quality, opt-in via ENABLE_SENTENCE_TRANSFORMERS=true
   because the model is a ~90MB download);
2. `gensim` Word2Vec trained on the local job-description corpus - a document
   vector is the mean of its word vectors (Word2Vec is trained here rather than
   downloaded so the pipeline works fully offline);
3. TF-IDF + Truncated SVD (latent semantic analysis) as a final fallback.

`SemanticModel.backend` is reported through the API so the UI can state which
model produced the numbers instead of implying a transformer was used.
"""
from __future__ import annotations

import numpy as np

from app.config import get_settings
from app.nlp.preprocessing import tokenize


class SemanticModel:
    def __init__(self, documents: list[str]) -> None:
        self.documents = documents
        self.backend = "none"
        self._st_model = None
        self._w2v = None
        self._svd_pipeline = None
        self._doc_vectors: np.ndarray | None = None
        if not documents:
            return
        if get_settings().enable_sentence_transformers and self._init_sentence_transformers():
            return
        if self._init_word2vec():
            return
        self._init_svd()

    # -- backends ---------------------------------------------------------
    def _init_sentence_transformers(self) -> bool:  # pragma: no cover - optional heavy dep
        try:
            from sentence_transformers import SentenceTransformer

            self._st_model = SentenceTransformer(get_settings().sentence_transformer_model)
            self._doc_vectors = np.asarray(self._st_model.encode(self.documents, normalize_embeddings=True))
            self.backend = "sentence-transformers"
            return True
        except Exception:
            self._st_model = None
            return False

    def _init_word2vec(self) -> bool:
        try:
            from gensim.models import Word2Vec
        except Exception:  # pragma: no cover - gensim always installed in practice
            return False
        corpus = [list(tokenize(doc)) for doc in self.documents]
        corpus = [tokens for tokens in corpus if tokens]
        if len(corpus) < 2:
            return False
        try:
            # Small corpus -> small window/dimension, min_count=1 so that rare but
            # meaningful skill tokens ("pyspark") are kept.
            self._w2v = Word2Vec(
                sentences=corpus, vector_size=100, window=5, min_count=1, workers=1, epochs=40, seed=42
            )
        except Exception:
            return False
        self._doc_vectors = np.vstack([self._mean_vector(doc) for doc in self.documents])
        self.backend = "word2vec"
        return True

    def _init_svd(self) -> None:
        from sklearn.decomposition import TruncatedSVD
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import Normalizer

        n_components = max(1, min(64, len(self.documents) - 1)) if len(self.documents) > 1 else 1
        pipeline = make_pipeline(
            TfidfVectorizer(min_df=1, token_pattern=r"(?u)\b[\w+#./-]{2,}\b"),
            TruncatedSVD(n_components=n_components, random_state=42),
            Normalizer(copy=False),
        )
        processed = [" ".join(tokenize(doc)) for doc in self.documents]
        try:
            self._doc_vectors = pipeline.fit_transform(processed)
            self._svd_pipeline = pipeline
            self.backend = "tfidf-svd"
        except Exception:
            self.backend = "none"

    # -- helpers ----------------------------------------------------------
    def _mean_vector(self, text: str) -> np.ndarray:
        assert self._w2v is not None
        tokens = [t for t in tokenize(text) if t in self._w2v.wv]
        if not tokens:
            return np.zeros(self._w2v.vector_size)
        return np.mean([self._w2v.wv[t] for t in tokens], axis=0)

    def encode(self, text: str) -> np.ndarray | None:
        if self.backend == "sentence-transformers" and self._st_model is not None:  # pragma: no cover
            return np.asarray(self._st_model.encode([text], normalize_embeddings=True))[0]
        if self.backend == "word2vec":
            return self._mean_vector(text)
        if self.backend == "tfidf-svd" and self._svd_pipeline is not None:
            return np.asarray(self._svd_pipeline.transform([" ".join(tokenize(text))]))[0]
        return None

    def similarity_to(self, query: str) -> list[float]:
        """Cosine similarity between `query` and every document (clipped to 0..1)."""
        if self._doc_vectors is None or self.backend == "none":
            return [0.0] * len(self.documents)
        vector = self.encode(query)
        if vector is None or not np.any(vector):
            return [0.0] * len(self.documents)
        docs = self._doc_vectors
        denom = np.linalg.norm(docs, axis=1) * np.linalg.norm(vector)
        with np.errstate(divide="ignore", invalid="ignore"):
            scores = np.where(denom > 0, docs @ vector / np.where(denom == 0, 1, denom), 0.0)
        return [round(float(np.clip(s, 0.0, 1.0)), 4) for s in scores]
