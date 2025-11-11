from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
from openai import OpenAI

try:
    import faiss  # type: ignore
except ImportError as exc:  # pragma: no cover - 서비스 초기화 단계에서 실패
    raise RuntimeError(
        "exercise_rag_service를 사용하려면 `faiss` 패키지가 필요합니다. "
        "`pip install faiss-cpu` 명령으로 설치하세요."
    ) from exc


class ExerciseRAGService:
    """운동 데이터 RAG 검색 서비스"""

    def __init__(
        self,
        index_path: Path = Path("data/exercise_index.faiss"),
        metadata_path: Path = Path("data/exercise_metadata.json"),
        embedding_model: str = "text-embedding-3-large",
        top_k: int = 5,
    ):
        if not index_path.exists() or not metadata_path.exists():
            raise FileNotFoundError(
                "FAISS 인덱스 또는 메타데이터 파일을 찾을 수 없습니다. "
                "scripts/build_exercise_index.py 스크립트를 먼저 실행하세요."
            )

        self.index = faiss.read_index(str(index_path))
        self.metadata: List[Dict[str, Any]] = json.loads(
            metadata_path.read_text(encoding="utf-8")
        )
        self.top_k = top_k
        self.embedding_model = embedding_model
        self.client = OpenAI()

    def search(self, query: str, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """질문과 유사한 운동 데이터를 검색합니다."""

        if not query.strip():
            return []

        k = top_k or self.top_k

        embedding_response = self.client.embeddings.create(
            model=self.embedding_model,
            input=query,
        )
        query_vector = np.array(embedding_response.data[0].embedding, dtype="float32")
        faiss.normalize_L2(query_vector.reshape(1, -1))

        scores, indices = self.index.search(query_vector.reshape(1, -1), k)

        results: List[Dict[str, Any]] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.metadata):
                continue
            metadata = self.metadata[idx]
            results.append(
                {
                    "score": float(score),
                    "title": metadata.get("title"),
                    "standard_title": metadata.get("standard_title"),
                    "training_name": metadata.get("training_name"),
                    "body_part": metadata.get("body_part"),
                    "exercise_tool": metadata.get("exercise_tool"),
                    "description": metadata.get("description"),
                    "video_url": metadata.get("video_url"),
                    "image_url": metadata.get("image_url"),
                }
            )

        return results


exercise_rag_service: Optional[ExerciseRAGService] = None


def get_exercise_rag_service() -> ExerciseRAGService:
    global exercise_rag_service

    if exercise_rag_service is None:
        exercise_rag_service = ExerciseRAGService()

    return exercise_rag_service

