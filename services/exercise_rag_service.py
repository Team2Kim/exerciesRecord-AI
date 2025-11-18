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

    def search(
        self, 
        query: str, 
        top_k: Optional[int] = None,
        target_group_filter: Optional[str] = None,
        exclude_target_groups: Optional[List[str]] = None,
        fitness_factor_filter: Optional[str] = None,
        exclude_fitness_factors: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        질문과 유사한 운동 데이터를 검색합니다.
        
        Args:
            query: 검색 쿼리
            top_k: 반환할 최대 결과 수
            target_group_filter: 원하는 대상 그룹 (예: "성인")
            exclude_target_groups: 제외할 대상 그룹 리스트 (예: ["유소년", "노인"])
            fitness_factor_filter: 원하는 체력 요인 (예: "근력/근지구력")
            exclude_fitness_factors: 제외할 체력 요인 리스트 (예: ["유연성"])
        """

        if not query.strip():
            return []

        k = top_k or self.top_k
        
        # 필터링이 필요한 경우 더 많은 결과를 검색 후 필터링
        # 필터링 후에도 충분한 결과를 얻기 위해 검색 수를 늘림
        search_k = k
        if target_group_filter or exclude_target_groups or fitness_factor_filter or exclude_fitness_factors:
            # 필터링이 있을 경우 3배 더 검색하여 필터링 후에도 충분한 결과 확보
            search_k = max(k * 3, 30)

        embedding_response = self.client.embeddings.create(
            model=self.embedding_model,
            input=query,
        )
        query_vector = np.array(embedding_response.data[0].embedding, dtype="float32")
        faiss.normalize_L2(query_vector.reshape(1, -1))

        scores, indices = self.index.search(query_vector.reshape(1, -1), search_k)

        results: List[Dict[str, Any]] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.metadata):
                continue
            meta = self.metadata[idx]
            
            # 필터링 적용
            target_group = meta.get("target_group")
            fitness_factor_name = meta.get("fitness_factor_name")
            
            # 대상 그룹 필터링
            if target_group_filter and target_group != target_group_filter:
                continue
            
            if exclude_target_groups:
                # 제외할 그룹이 있으면 해당 그룹은 건너뛰기
                # None이나 빈 문자열도 체크하여 명시적으로 제외 그룹인 경우만 필터링
                if target_group and target_group in exclude_target_groups:
                    continue
            
            # 체력 요인 필터링
            if fitness_factor_filter and fitness_factor_name != fitness_factor_filter:
                continue
            
            if exclude_fitness_factors:
                # 제외할 체력 요인이 있으면 해당 요인은 건너뛰기
                if fitness_factor_name and fitness_factor_name in exclude_fitness_factors:
                    continue
            
            metadata = {
                "exercise_id": meta.get("exercise_id"),
                "title": meta.get("title"),
                "standard_title": meta.get("standard_title"),
                "training_name": meta.get("training_name"),
                "body_part": meta.get("body_part"),
                "exercise_tool": meta.get("exercise_tool"),
                "fitness_factor_name": fitness_factor_name,
                "fitness_level_name": meta.get("fitness_level_name"),
                "target_group": target_group,
                "training_aim_name": meta.get("training_aim_name"),
                "training_place_name": meta.get("training_place_name"),
                "training_section_name": meta.get("training_section_name"),
                "training_step_name": meta.get("training_step_name"),
                "description": meta.get("description"),
                "muscles": meta.get("muscles"),  # 근육 정보 추가
                "video_url": meta.get("video_url"),
                "video_length_seconds": meta.get("video_length_seconds"),
                "image_url": meta.get("image_url"),
                "image_file_name": meta.get("image_file_name"),
            }
            results.append(
                {
                    "score": float(score),
                    "metadata": metadata,
                }
            )
            
            # 필터링 후 원하는 개수만큼 모이면 종료
            if len(results) >= k:
                break

        return results


exercise_rag_service: Optional[ExerciseRAGService] = None


def get_exercise_rag_service() -> ExerciseRAGService:
    global exercise_rag_service

    if exercise_rag_service is None:
        exercise_rag_service = ExerciseRAGService()

    return exercise_rag_service

