import argparse
from pathlib import Path

from services.rag_pipeline import refresh_rag_assets


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the RAG embedding pipeline.")
    parser.add_argument(
        "--source",
        choices=["mysql", "csv"],
        default="mysql",
        help="데이터 소스 (mysql 또는 csv)",
    )
    parser.add_argument(
        "--csv-path",
        type=Path,
        default=Path("exercises_muscle.csv"),
        help="CSV 사용 시 입력 파일 경로",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="기존 인덱스가 있어도 강제로 재생성",
    )
    parser.add_argument(
        "--no-skip-if-exists",
        action="store_true",
        help="인덱스가 있어도 건너뛰지 않음",
    )
    parser.add_argument(
        "--embedding-model",
        type=str,
        default=None,
        help="임베딩에 사용할 OpenAI 모델 (기본: text-embedding-3-large)",
    )
    parser.add_argument(
        "--embedding-batch-size",
        type=int,
        default=None,
        help="임베딩 호출 배치 사이즈",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    refresh_rag_assets(
        source=args.source,
        csv_path=str(args.csv_path),
        force=args.force,
        skip_if_exists=not args.no_skip_if_exists,
        embedding_model=args.embedding_model,
        embedding_batch_size=args.embedding_batch_size,
    )


if __name__ == "__main__":
    main()


