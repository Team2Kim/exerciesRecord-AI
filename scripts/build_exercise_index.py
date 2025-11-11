import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
from openai import OpenAI
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

try:
    import faiss  # type: ignore
except ImportError as exc:  # pragma: no cover - script time error
    raise SystemExit(
        "faiss 패키지가 필요합니다. `pip install faiss-cpu` 명령으로 설치해주세요."
    ) from exc


DEFAULT_INPUT = Path("data/processed_exercises.jsonl")
DEFAULT_INDEX = Path("data/exercise_index.faiss")
DEFAULT_METADATA = Path("data/exercise_metadata.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create FAISS index from preprocessed exercise JSONL."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help="전처리된 JSONL 경로 (processed_exercises.jsonl).",
    )
    parser.add_argument(
        "--index-output",
        type=Path,
        default=DEFAULT_INDEX,
        help="생성할 FAISS 인덱스 파일 경로.",
    )
    parser.add_argument(
        "--metadata-output",
        type=Path,
        default=DEFAULT_METADATA,
        help="메타데이터 JSON 파일 경로.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="text-embedding-3-large",
        help="OpenAI 임베딩 모델명.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="임베딩 API 호출 배치 크기.",
    )
    return parser.parse_args()


def load_records(jsonl_path: Path) -> List[Dict[str, Any]]:
    if not jsonl_path.exists():
        raise FileNotFoundError(f"JSONL 파일을 찾을 수 없습니다: {jsonl_path}")

    records: List[Dict[str, Any]] = []
    with jsonl_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))

    if not records:
        raise ValueError("JSONL 파일에서 데이터를 찾을 수 없습니다.")

    return records


def chunk_iter(data: List[Any], size: int) -> List[List[Any]]:
    for i in range(0, len(data), size):
        yield data[i : i + size]


def build_embeddings(
    client: OpenAI, texts: List[str], model: str, batch_size: int
) -> List[List[float]]:
    embeddings: List[List[float]] = []
    for batch in chunk_iter(texts, batch_size):
        response = client.embeddings.create(model=model, input=batch)
        for item in response.data:
            embeddings.append(item.embedding)
    return embeddings


def create_faiss_index(vectors: np.ndarray) -> faiss.IndexFlatIP:
    faiss.normalize_L2(vectors)
    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)
    return index


def main() -> None:
    args = parse_args()
    client = OpenAI()

    records = load_records(args.input)
    texts = [record["text"] for record in records]

    print(f"총 {len(texts)}개 레코드 임베딩 생성 중...", file=sys.stderr)
    embeddings = build_embeddings(client, texts, args.model, args.batch_size)

    vectors = np.array(embeddings, dtype="float32")
    index = create_faiss_index(vectors)

    args.index_output.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(args.index_output))

    metadata = [
        {"id": record.get("id"), **record.get("metadata", {})} for record in records
    ]
    args.metadata_output.parent.mkdir(parents=True, exist_ok=True)
    args.metadata_output.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(
        f"인덱스 생성 완료. 레코드: {len(metadata)} | "
        f"Index -> {args.index_output} | Metadata -> {args.metadata_output}"
    )


if __name__ == "__main__":
    main()

