import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Preprocess exercise CSV file for RAG ingestion."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("exercises_muscle.csv"),
        help="Path to the raw CSV file.",
    )
    parser.add_argument(
        "--output-jsonl",
        type=Path,
        default=Path("data/processed_exercises.jsonl"),
        help="Destination path for the generated JSONL file.",
    )
    parser.add_argument(
        "--output-parquet",
        type=Path,
        default=Path("data/processed_exercises.parquet"),
        help="Destination path for the processed parquet file.",
    )
    parser.add_argument(
        "--encoding",
        type=str,
        default=None,
        help="Encoding for reading the CSV (auto-detected if omitted).",
    )
    return parser.parse_args()


def detect_encoding(csv_path: Path) -> str:
    candidates = ["cp949", "utf-8-sig", "utf-8"]
    for enc in candidates:
        try:
            csv_path.open("r", encoding=enc).read(1024)
            return enc
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError(
        "encoding", b"", 0, 1, "Unable to detect encoding automatically."
    )


def load_dataframe(csv_path: Path, encoding: Optional[str]) -> pd.DataFrame:
    enc = encoding or detect_encoding(csv_path)
    try:
        df = pd.read_csv(csv_path, encoding=enc, dtype=str, quoting=csv.QUOTE_MINIMAL)
    except UnicodeDecodeError as exc:
        raise RuntimeError(f"Failed to read CSV with encoding {enc}") from exc

    # Strip whitespace and normalise empty strings.
    for col in df.columns:
        df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)
    df = df.fillna("")
    return df


TEXT_FIELDS = [
    "title",
    "standard_title",
    "training_name",
    "body_part",
    "exercise_tool",
    "fitness_factor_name",
    "fitness_level_name",
    "target_group",
    "training_aim_name",
    "training_place_name",
    "training_section_name",
    "training_step_name",
    "description",
    "image_url",
    "video_url",
    "muscles",  # 근육 정보 추가
]

# 메타데이터에만 포함되는 필드 (임베딩 텍스트에는 포함하지 않음)
METADATA_ONLY_FIELDS = [
    "exercise_id",
    "video_length_seconds",
    "image_file_name",
]


def build_chunk(row: Dict[str, str]) -> str:
    lines: List[str] = []
    append = lines.append

    title = row.get("title") or row.get("standard_title") or "알 수 없는 운동"
    append(f"운동명: {title}")

    if row.get("standard_title"):
        append(f"표준 제목: {row['standard_title']}")
    if row.get("training_name"):
        append(f"훈련 프로그램: {row['training_name']}")
    if row.get("body_part"):
        append(f"운동 부위: {row['body_part']}")
    if row.get("exercise_tool"):
        append(f"운동 도구: {row['exercise_tool']}")
    if row.get("fitness_level_name"):
        append(f"운동 수준: {row['fitness_level_name']}")
    if row.get("fitness_factor_name"):
        append(f"운동 요소: {row['fitness_factor_name']}")
    if row.get("target_group"):
        append(f"대상자: {row['target_group']}")
    if row.get("training_aim_name"):
        append(f"훈련 목적: {row['training_aim_name']}")
    if row.get("training_place_name"):
        append(f"훈련 장소: {row['training_place_name']}")
    if row.get("training_section_name"):
        append(f"훈련 구간: {row['training_section_name']}")
    if row.get("training_step_name"):
        append(f"훈련 단계: {row['training_step_name']}")
    if row.get("description"):
        append(f"설명: {row['description']}")
    if row.get("muscles"):
        append(f"타겟 근육: {row['muscles']}")
    if row.get("video_url"):
        append(f"영상 링크: {row['video_url']}")

    return "\n".join(lines)


def preprocess_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    # Keep only relevant columns to reduce noise.
    # TEXT_FIELDS는 임베딩 텍스트에 사용, METADATA_ONLY_FIELDS는 메타데이터에만 사용
    all_fields = TEXT_FIELDS + METADATA_ONLY_FIELDS
    available_cols = [col for col in all_fields if col in df.columns]
    subset = df[available_cols].copy()

    subset["chunk_text"] = subset.apply(lambda row: build_chunk(row.to_dict()), axis=1)

    # Basic deduplication on chunk text.
    subset = subset.drop_duplicates(subset=["chunk_text"]).reset_index(drop=True)
    return subset


def export_jsonl(df: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        for idx, row in df.iterrows():
            # TEXT_FIELDS와 METADATA_ONLY_FIELDS 모두 메타데이터에 포함
            all_metadata_fields = TEXT_FIELDS + METADATA_ONLY_FIELDS
            metadata = {}
            for key in all_metadata_fields:
                if key in row:
                    value = row.get(key)
                    # 빈 문자열이 아닌 경우만 포함
                    if value and str(value).strip():
                        metadata[key] = value
            
            record = {
                "id": idx,
                "text": row["chunk_text"],
                "metadata": metadata,
            }
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def export_parquet(df: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)


def main() -> None:
    args = parse_args()
    df_raw = load_dataframe(args.input, args.encoding)
    df_processed = preprocess_dataframe(df_raw)

    export_jsonl(df_processed, args.output_jsonl)
    export_parquet(df_processed, args.output_parquet)

    print(
        f"Preprocessing complete. Records: {len(df_processed)} | "
        f"JSONL -> {args.output_jsonl} | Parquet -> {args.output_parquet}"
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print(f"[ERROR] {err}", file=sys.stderr)
        sys.exit(1)

