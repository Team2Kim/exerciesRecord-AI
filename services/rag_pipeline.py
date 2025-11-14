from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Literal, Optional, List, Dict

import pandas as pd

from services.mysql_service import MySQLService
from scripts.preprocess_exercises import (
    TEXT_FIELDS,
    METADATA_ONLY_FIELDS,
    preprocess_dataframe,
    export_jsonl,
    export_parquet,
    load_dataframe,
)


DEFAULT_PROCESSED_JSONL = Path("data/processed_exercises.jsonl")
DEFAULT_PROCESSED_PARQUET = Path("data/processed_exercises.parquet")
DEFAULT_INDEX_PATH = Path("data/exercise_index.faiss")
DEFAULT_METADATA_PATH = Path("data/exercise_metadata.json")


def _load_from_mysql() -> pd.DataFrame:
    service = MySQLService()
    try:
        rows = service.fetch_exercises_for_rag()
    finally:
        service.close()

    if not rows:
        raise RuntimeError("MySQL에서 운동 데이터를 찾을 수 없습니다.")

    df = pd.DataFrame(rows)

    for column in TEXT_FIELDS + METADATA_ONLY_FIELDS:
        if column not in df.columns:
            df[column] = ""
        else:
            df[column] = df[column].fillna("").astype(str)

    return df


def _load_from_csv(csv_path: Path) -> pd.DataFrame:
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV 파일을 찾을 수 없습니다: {csv_path}")
    return load_dataframe(csv_path, encoding=None)


def _run_embedding_builder(input_path: Path, model: Optional[str] = None, batch_size: Optional[int] = None) -> None:
    command: List[str] = [sys.executable, "scripts/build_exercise_index.py", "--input", str(input_path)]

    if model:
        command.extend(["--model", model])
    if batch_size:
        command.extend(["--batch-size", str(batch_size)])

    subprocess.run(command, check=True)


def refresh_rag_assets(
    source: Literal["mysql", "csv"] = "mysql",
    csv_path: Optional[str] = None,
    force: bool = False,
    skip_if_exists: bool = True,
    embedding_model: Optional[str] = None,
    embedding_batch_size: Optional[int] = None,
) -> None:
    """
    DB 또는 CSV에서 최신 운동 데이터를 가져와 임베딩 파이프라인을 수행합니다.
    """

    index_exists = DEFAULT_INDEX_PATH.exists() and DEFAULT_METADATA_PATH.exists()
    if skip_if_exists and index_exists and not force:
        print("✅ 기존 FAISS 인덱스가 있어 파이프라인을 건너뜁니다.")
        return

    if source == "mysql":
        print("📥 MySQL에서 운동 데이터를 불러오는 중...")
        df_raw = _load_from_mysql()
    else:
        csv_file = Path(csv_path or "exercises_muscle.csv")
        print(f"📥 CSV ({csv_file})에서 운동 데이터를 불러오는 중...")
        df_raw = _load_from_csv(csv_file)

    print("🧹 전처리 수행 중...")
    processed_df = preprocess_dataframe(df_raw)
    export_jsonl(processed_df, DEFAULT_PROCESSED_JSONL)
    export_parquet(processed_df, DEFAULT_PROCESSED_PARQUET)

    print("🧠 OpenAI 임베딩 및 FAISS 인덱스 생성 중...")
    _run_embedding_builder(
        input_path=DEFAULT_PROCESSED_JSONL,
        model=embedding_model,
        batch_size=embedding_batch_size,
    )

    print("✨ RAG 파이프라인 갱신 완료!")


def refresh_rag_assets_from_env() -> None:
    """
    환경변수 기반으로 파이프라인을 실행합니다.
    """
    should_run = os.getenv("REFRESH_RAG_ON_START") == "1"
    if not should_run:
        return

    source = os.getenv("RAG_PIPELINE_SOURCE", "mysql").lower()
    csv_path = os.getenv("RAG_PIPELINE_CSV_PATH")
    force = os.getenv("FORCE_RAG_REFRESH") == "1"
    skip_if_exists = os.getenv("RAG_SKIP_IF_EXISTS", "1") == "1"
    embedding_model = os.getenv("RAG_EMBEDDING_MODEL")
    batch_size_env = os.getenv("RAG_EMBEDDING_BATCH_SIZE")
    embedding_batch_size = int(batch_size_env) if batch_size_env else None

    refresh_rag_assets(
        source="mysql" if source not in {"mysql", "csv"} else source,  # 기본 mysql
        csv_path=csv_path,
        force=force,
        skip_if_exists=skip_if_exists,
        embedding_model=embedding_model,
        embedding_batch_size=embedding_batch_size,
    )


__all__ = ["refresh_rag_assets", "refresh_rag_assets_from_env"]


