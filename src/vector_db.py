from dataclasses import dataclass
import math


@dataclass
class IndexedChunk:
    text: str
    embedding: list[float]
    metadata: dict[str, object]


class VectorDB:
    def build_index(self, chunks: list[dict]) -> None:
        raise NotImplementedError

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 3,
        filters: dict | None = None,
    ) -> list[dict]:
        raise NotImplementedError


class MockVectorDB(VectorDB):
    def __init__(self) -> None:
        self._chunks: list[IndexedChunk] = []

    def build_index(self, chunks: list[dict]) -> None:
        self._chunks = [
            IndexedChunk(
                text=str(chunk["text"]),
                embedding=list(chunk["embedding"]),
                metadata=dict(chunk["metadata"]),
            )
            for chunk in chunks
        ]

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 3,
        filters: dict | None = None,
    ) -> list[dict]:
        scored: list[dict] = []
        for chunk in self._chunks:
            if filters and not self._matches_filters(chunk.metadata, filters):
                continue
            score = self._cosine_similarity(query_embedding, chunk.embedding)
            scored.append({"text": chunk.text, "score": score, "metadata": chunk.metadata})

        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored[:top_k]

    def _matches_filters(self, metadata: dict[str, object], filters: dict) -> bool:
        for key, expected in filters.items():
            if expected in (None, "", []):
                continue
            actual = metadata.get(key)
            if isinstance(actual, list):
                if expected not in actual:
                    return False
            elif actual != expected:
                return False
        return True

    def _cosine_similarity(self, left: list[float], right: list[float]) -> float:
        length = min(len(left), len(right))
        if length == 0:
            return 0.0
        dot = sum(left[index] * right[index] for index in range(length))
        left_norm = math.sqrt(sum(value * value for value in left)) or 1.0
        right_norm = math.sqrt(sum(value * value for value in right)) or 1.0
        return dot / (left_norm * right_norm)


FAISSVectorDB = MockVectorDB
