from pathlib import Path
import re

from .embedding_client import BaseEmbeddingClient
from .vector_db import VectorDB


class Retriever:
    def __init__(self, embedding_client: BaseEmbeddingClient, vector_db: VectorDB) -> None:
        self.embedding_client = embedding_client
        self.vector_db = vector_db

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
        filters: dict | None = None,
    ) -> list[dict]:
        query_embedding = self.embedding_client.embed_text(query)
        return self.vector_db.search(query_embedding=query_embedding, top_k=top_k, filters=filters)

    def search(self, query: str, agent_id: str | None = None, top_k: int = 4) -> list[dict[str, object]]:
        filters = {"agent_scope": agent_id} if agent_id else None
        results = self.retrieve(query=query, top_k=top_k, filters=filters)
        if len(results) < top_k and filters:
            seen = {item["metadata"]["chunk_id"] for item in results}
            broad_results = self.retrieve(query=query, top_k=top_k, filters=None)
            for item in broad_results:
                if item["metadata"]["chunk_id"] not in seen:
                    results.append(item)
                if len(results) >= top_k:
                    break

        return [
            {
                "source": item["metadata"].get("source_path"),
                "content": item["text"],
                "score": round(float(item["score"]), 4),
                "metadata": item["metadata"],
            }
            for item in results[:top_k]
        ]


class RAGIndexBuilder:
    INDEX_EXTENSIONS = {".md", ".yaml", ".yml"}

    def __init__(self, base_dir: str | Path, embedding_client: BaseEmbeddingClient) -> None:
        self.base_dir = Path(base_dir)
        self.embedding_client = embedding_client

    def build_chunks(self) -> list[dict]:
        chunks: list[dict] = []
        for root_name in ("data", "shared", "agents"):
            root = self.base_dir / root_name
            if not root.exists():
                continue
            for path in sorted(root.rglob("*")):
                if path.is_file() and path.suffix in self.INDEX_EXTENSIONS:
                    chunks.extend(self._chunk_file(path))
        return chunks

    def _chunk_file(self, path: Path) -> list[dict]:
        text = path.read_text(encoding="utf-8")
        raw_chunks = [chunk.strip() for chunk in re.split(r"\n\s*\n", text) if len(chunk.strip()) > 20]
        relative_source = path.relative_to(self.base_dir).as_posix()
        document_id = path.stem
        module_id = self._module_id(relative_source)
        agent_scope = self._agent_scope(relative_source)

        chunks = []
        for index, chunk in enumerate(raw_chunks, start=1):
            chunk_id = f"{document_id}_{index:03d}"
            chunks.append(
                {
                    "text": chunk,
                    "embedding": self.embedding_client.embed_text(chunk + " " + relative_source),
                    "metadata": {
                        "document_id": document_id,
                        "chunk_id": chunk_id,
                        "module_id": module_id,
                        "agent_scope": agent_scope,
                        "content_type": self._content_type(relative_source),
                        "source_path": relative_source,
                        "token_count": len(chunk.split()),
                    },
                }
            )
        return chunks

    def _module_id(self, source_path: str) -> str | None:
        if "module_1" in source_path or "group_dna" in source_path:
            return "module_1"
        if "module_2" in source_path or "360" in source_path or "coaching" in source_path:
            return "module_2"
        if "module_3" in source_path or "rollout" in source_path or "regional" in source_path:
            return "module_3"
        return None

    def _agent_scope(self, source_path: str) -> list[str]:
        if "gucci_group_ceo" in source_path:
            return ["gucci_group_ceo"]
        if "gucci_group_chro" in source_path:
            return ["gucci_group_chro"]
        if "regional_comms_manager" in source_path:
            return ["regional_comms_manager"]
        if "module_1" in source_path or "group_dna" in source_path:
            return ["gucci_group_ceo", "gucci_group_chro"]
        if "module_2" in source_path or "360" in source_path or "coaching" in source_path:
            return ["gucci_group_chro"]
        if "module_3" in source_path or "rollout" in source_path:
            return ["regional_comms_manager", "gucci_group_chro"]
        return ["gucci_group_ceo", "gucci_group_chro", "regional_comms_manager"]

    def _content_type(self, source_path: str) -> str:
        if source_path.startswith("agents/"):
            return "agent_config"
        if source_path.startswith("shared/"):
            return "shared_config"
        return "simulation_document"


def create_default_retriever(base_dir: str | Path, embedding_client: BaseEmbeddingClient, vector_db: VectorDB) -> Retriever:
    chunks = RAGIndexBuilder(base_dir, embedding_client).build_chunks()
    vector_db.build_index(chunks)
    return Retriever(embedding_client=embedding_client, vector_db=vector_db)


RAGRetriever = Retriever
KeywordRetriever = Retriever
