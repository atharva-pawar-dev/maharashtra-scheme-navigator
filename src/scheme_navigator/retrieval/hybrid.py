
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Protocol

try:
    from rank_bm25 import BM25Okapi
except ImportError:

    class BM25Okapi:  # type: ignore[no-redef]
        """Small deterministic BM25 fallback for local development."""

        def __init__(
            self,
            corpus: list[list[str]],
            k1: float = 1.5,
            b: float = 0.75,
        ) -> None:
            self.corpus = corpus
            self.k1 = k1
            self.b = b
            self.lengths = [len(doc) for doc in corpus]
            self.avgdl = sum(self.lengths) / max(1, len(self.lengths))
            self.tf = [Counter(doc) for doc in corpus]
            self.df = Counter(
                token
                for doc in corpus
                for token in set(doc)
            )

        def get_scores(self, query_tokens: list[str]) -> list[float]:
            scores: list[float] = []
            n = len(self.corpus)

            for tf, length in zip(self.tf, self.lengths):
                score = 0.0

                for token in query_tokens:
                    freq = tf.get(token, 0)
                    if freq == 0:
                        continue

                    df = self.df[token]
                    idf = math.log(
                        1.0 + (n - df + 0.5) / (df + 0.5)
                    )

                    length_norm = (
                        1.0 - self.b
                        + self.b * length / max(1.0, self.avgdl)
                    )
                    denominator = freq + self.k1 * length_norm

                    score += (
                        idf
                        * freq
                        * (self.k1 + 1.0)
                        / denominator
                    )

                scores.append(score)

            return scores


@dataclass(frozen=True)
class RetrievalDocument:
    doc_id: str
    title: str
    text: str
    source_url: str
    source_type: str


@dataclass(frozen=True)
class SearchHit:
    doc: RetrievalDocument
    score: float
    bm25_rank: int | None = None
    semantic_rank: int | None = None


class SemanticRetriever(Protocol):
    def search(
        self,
        query: str,
        limit: int = 10,
    ) -> list[tuple[str, float]]:
        ...


def tokenize(text: str) -> list[str]:
    """Keep Unicode letters and digits for Marathi, Hindi and English."""
    return re.findall(r"[^\W_]+", text.casefold(), flags=re.UNICODE)


def reciprocal_rank_fusion(
    *ranked_lists: list[tuple[str, float]],
    k: int = 60,
) -> dict[str, float]:
    """Fuse ranked results without depending on raw score scales."""
    fused: dict[str, float] = {}

    for result_list in ranked_lists:
        for rank, (doc_id, _score) in enumerate(result_list, start=1):
            fused[doc_id] = (
                fused.get(doc_id, 0.0)
                + 1.0 / (k + rank)
            )

    return fused


class HybridRetriever:
    """BM25 retrieval with optional semantic search and rank fusion."""

    def __init__(
        self,
        documents: list[RetrievalDocument],
        semantic: SemanticRetriever | None = None,
    ) -> None:
        # Deduplicate IDs first so document IDs and the BM25 corpus
        # always have the same ordering and length.
        self.documents = {
            doc.doc_id: doc
            for doc in documents
        }
        self._ids = list(self.documents)

        corpus = [
            tokenize(
                f"{self.documents[doc_id].title} "
                f"{self.documents[doc_id].text}"
            )
            for doc_id in self._ids
        ]

        self._token_sets = {
            doc_id: set(tokens)
            for doc_id, tokens in zip(self._ids, corpus)
        }

        self._bm25 = BM25Okapi(corpus) if corpus else None
        self._semantic = semantic

    def search(self, query: str, limit: int = 10) -> list[SearchHit]:
        if limit < 1 or limit > 100:
            raise ValueError("limit must be in [1, 100]")

        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        bm25_ranked: list[tuple[str, float]] = []

        if self._bm25 is not None:
            scores = self._bm25.get_scores(query_tokens)
            query_set = set(query_tokens)

            # Keep lexical overlap separate from the statistical score.
            # With a tiny corpus, BM25 can score a genuinely matching
            # document as zero. Excluding scores <= 0 loses that match.
            candidates: list[tuple[str, float, int]] = []

            for index, raw_score in enumerate(scores):
                doc_id = self._ids[index]
                overlap = len(
                    query_set & self._token_sets[doc_id]
                )

                # Never return a BM25 candidate with no query-term overlap.
                if overlap == 0:
                    continue

                candidates.append(
                    (doc_id, float(raw_score), overlap)
                )

            # BM25 score remains the primary ranking signal.
            # Lexical overlap breaks ties, including zero-score ties.
            candidates.sort(
                key=lambda item: (item[1], item[2]),
                reverse=True,
            )

            bm25_ranked = [
                (doc_id, score)
                for doc_id, score, _overlap in candidates[:limit]
            ]

        semantic_ranked: list[tuple[str, float]] = []

        if self._semantic is not None:
            semantic_ranked = [
                (doc_id, float(score))
                for doc_id, score in self._semantic.search(query, limit)
                if doc_id in self.documents
            ][:limit]

        # Fuse rankings only. Unknown semantic document IDs must not
        # appear in the returned results.
        if semantic_ranked:
            fused = reciprocal_rank_fusion(
                bm25_ranked,
                semantic_ranked,
            )
        else:
            fused = {
                doc_id: 1.0 / (60 + rank)
                for rank, (doc_id, _score) in enumerate(
                    bm25_ranked,
                    start=1,
                )
            }

        bm25_positions = {
            doc_id: rank
            for rank, (doc_id, _score) in enumerate(
                bm25_ranked,
                start=1,
            )
        }

        semantic_positions = {
            doc_id: rank
            for rank, (doc_id, _score) in enumerate(
                semantic_ranked,
                start=1,
            )
        }

        ranked = sorted(
            fused.items(),
            key=lambda item: item[1],
            reverse=True,
        )[:limit]

        return [
            SearchHit(
                doc=self.documents[doc_id],
                score=score,
                bm25_rank=bm25_positions.get(doc_id),
                semantic_rank=semantic_positions.get(doc_id),
            )
            for doc_id, score in ranked
            if doc_id in self.documents
        ]
