from __future__ import annotations

import csv
import warnings
from pathlib import Path

import pandas as pd

try:
    from tqdm import tqdm
except ImportError:
    tqdm = lambda iterable: iterable


REQUIRED_COLUMNS = {
    "PARTICIPANT_ID",
    "TEST_SECTION_ID",
    "SENTENCE",
    "USER_INPUT",
    "KEYSTROKE_ID",
    "PRESS_TIME",
    "RELEASE_TIME",
    "LETTER",
    "KEYCODE",
}


def discover_input_files(data_dir: str | Path) -> list[Path]:
    """Return supported raw data files from a file or directory path."""
    path = Path(data_dir)
    if path.is_file():
        return [path]
    if not path.exists():
        raise FileNotFoundError(f"Input path does not exist: {path}")

    files: list[Path] = []
    for pattern in ("*.txt", "*.tsv", "*.csv"):
        files.extend(path.rglob(pattern))
    return sorted(set(files))


def load_typing_logs(data_dir: str | Path) -> pd.DataFrame:
    """Load one file or a directory of sample_file-like TSV/CSV files."""
    frames: list[pd.DataFrame] = []
    skipped_files: list[tuple[Path, str]] = []
    for file_path in tqdm(discover_input_files(data_dir), desc="loading raw files"):
        separator = "," if file_path.suffix.lower() == ".csv" else "\t"
        try:
            frame = pd.read_csv(
                file_path,
                sep=separator,
                dtype={"LETTER": "string"},
                encoding="utf-8-sig",
                quoting=csv.QUOTE_NONE,
                on_bad_lines="warn",
            )
        except UnicodeDecodeError as error:
            skipped_files.append((file_path, f"encoding error: {error}"))
            continue

        missing = REQUIRED_COLUMNS.difference(frame.columns)
        if missing:
            skipped_files.append((file_path, f"missing columns: {sorted(missing)}"))
            continue
        frame["SOURCE_FILE"] = str(file_path)
        frames.append(frame)

    if not frames:
        skipped = "\n".join(f"- {path}: {reason}" for path, reason in skipped_files)
        raise ValueError(
            f"No readable .txt, .tsv, or .csv files found in {data_dir}.\n{skipped}"
        )

    raw = pd.concat(frames, ignore_index=True)
    raw["PRESS_TIME"] = pd.to_numeric(raw["PRESS_TIME"], errors="coerce")
    raw["RELEASE_TIME"] = pd.to_numeric(raw["RELEASE_TIME"], errors="coerce")
    raw["KEYSTROKE_ID"] = pd.to_numeric(raw["KEYSTROKE_ID"], errors="coerce")
    raw["KEYCODE"] = pd.to_numeric(raw["KEYCODE"], errors="coerce")
    raw = raw.dropna(subset=["PRESS_TIME", "RELEASE_TIME", "KEYSTROKE_ID", "KEYCODE"])
    if skipped_files:
        skipped = "\n".join(f"- {path}: {reason}" for path, reason in skipped_files)
        warnings.warn(f"Skipped {len(skipped_files)} input file(s):\n{skipped}", stacklevel=2)
    return raw
