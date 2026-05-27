from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from tqdm import tqdm
import pandas as pd
from scipy import sparse
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors

from text_processing import extract_missed_words, trigram_counts, trigram_document, word_trigrams


@dataclass
class Recommendation:
    word: str
    score: float
    frequency: float
    matched_trigrams: str


class TypingErrorRecommender:
    """TF-IDF trigram recommender for words a user is likely to misspell."""

    def __init__(self, max_features: int | None = None) -> None:
        self.vectorizer = TfidfVectorizer(
            analyzer="word",
            token_pattern=r"(?u)\b[a-z]{3}\b",
            lowercase=False,
            max_features=max_features,
        )
        self.trigram_index: dict[str, int] = {}
        self.trigram_vector_store: sparse.csr_matrix | None = None
        self.trigram_neighbors: NearestNeighbors | None = None
        self.word_index: pd.DataFrame | None = None

    def fit(self, user_profiles: pd.DataFrame, vocabulary_words: list[str]) -> "TypingErrorRecommender":
        self.vectorizer.fit(user_profiles["error_trigrams"].fillna(""))
        self.trigram_index = dict(sorted(self.vectorizer.vocabulary_.items(), key=lambda item: item[1]))
        self._fit_trigram_vector_store()
        self.word_index = self._build_word_index(vocabulary_words)
        return self

    def recommend_from_attempts(
        self,
        attempts: pd.DataFrame,
        last_n: int | None = None,
        top_k: int = 50,
        trigram_k: int = 100,
    ) -> pd.DataFrame:
        attempts = attempts.copy()
        if last_n is not None and last_n > 0:
            attempts = attempts.tail(last_n)

        missed_words: list[str] = []
        for _, row in attempts.iterrows():
            missed_words.extend(extract_missed_words(row["target"], row["typed"]))
        return self.recommend_from_error_words(missed_words, top_k=top_k, trigram_k=trigram_k)

    def recommend_from_error_words(
        self,
        missed_words: list[str],
        top_k: int = 50,
        trigram_k: int = 100,
    ) -> pd.DataFrame:
        query_doc = trigram_document(missed_words)
        if not query_doc:
            return pd.DataFrame(columns=["word", "score", "frequency", "matched_trigrams"])

        query_vector = self.vectorizer.transform([query_doc])
        trigram_weights = self._query_trigram_weights(query_vector, top_k=trigram_k)
        return self.rank_words(trigram_weights, top_k=top_k)

    def rank_words(self, trigram_weights: dict[str, float], top_k: int = 50) -> pd.DataFrame:
        if self.word_index is None:
            raise ValueError("Recommender is not fitted with a word index.")
        if not trigram_weights:
            return pd.DataFrame(columns=["word", "score", "frequency", "matched_trigrams"])

        rows: list[Recommendation] = []
        for row in self.word_index.itertuples(index=False):
            word_counts: dict[str, int] = row.trigram_counts
            matched = {
                trigram: trigram_weights[trigram] * count
                for trigram, count in word_counts.items()
                if trigram in trigram_weights
            }
            if not matched:
                continue
            raw_score = sum(matched.values())
            normalized_score = raw_score / max(len(row.trigrams), 1)
            rows.append(
                Recommendation(
                    word=row.word,
                    score=float(normalized_score),
                    frequency=0.0,
                    matched_trigrams=" ".join(sorted(matched, key=matched.get, reverse=True)),
                )
            )

        result = pd.DataFrame([row.__dict__ for row in rows])
        if result.empty:
            return pd.DataFrame(columns=["word", "score", "frequency", "matched_trigrams"])
        result = result.sort_values(["score", "word"], ascending=[False, True]).head(top_k).reset_index(drop=True)
        score_sum = float(result["score"].sum())
        if score_sum > 0:
            result["frequency"] = result["score"] / score_sum
        return result

    def _query_trigram_weights(self, query_vector: sparse.csr_matrix, top_k: int) -> dict[str, float]:
        if self.trigram_neighbors is None or self.trigram_vector_store is None:
            raise ValueError("Trigram vector store is not fitted.")

        available = self.trigram_vector_store.shape[0]
        k = max(1, min(top_k, available))
        distances, indices = self.trigram_neighbors.kneighbors(query_vector, n_neighbors=k)
        inverse_vocab = {index: trigram for trigram, index in self.vectorizer.vocabulary_.items()}
        query_weights = query_vector.toarray()[0]
        weights: dict[str, float] = {}

        for distance, feature_index in zip(distances[0], indices[0]):
            trigram = inverse_vocab[int(feature_index)]
            tfidf_weight = float(query_weights[int(feature_index)])
            similarity = max(0.0, 1.0 - float(distance))
            if tfidf_weight > 0:
                weights[trigram] = tfidf_weight * similarity
        return weights

    def _fit_trigram_vector_store(self) -> None:
        feature_count = len(self.vectorizer.vocabulary_)
        self.trigram_vector_store = sparse.identity(feature_count, format="csr")
        self.trigram_neighbors = NearestNeighbors(metric="cosine", algorithm="brute")
        self.trigram_neighbors.fit(self.trigram_vector_store)

    def _build_word_index(self, vocabulary_words: list[str]) -> pd.DataFrame:
        rows: list[dict[str, object]] = []
        for word in vocabulary_words:
            trigrams = [trigram for trigram in word_trigrams(word) if trigram in self.vectorizer.vocabulary_]
            if not trigrams:
                continue
            rows.append(
                {
                    "word": word,
                    "trigrams": trigrams,
                    "trigram_counts": dict(trigram_counts([word])),
                }
            )
        if not rows:
            raise ValueError("No dictionary words share trigrams with the trained user profiles.")
        return pd.DataFrame(rows)


def load_vocabulary(path: str | Path) -> list[str]:
    words: list[str] = []
    for line in tqdm(Path(path).read_text(encoding="utf-8").splitlines(), desc='loading vocabulary'):
        word = line.strip().lower()
        if word.isalpha() and len(word) >= 3:
            words.append(word)
    return words
