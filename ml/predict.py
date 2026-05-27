from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import pandas as pd

from data_loader import load_typing_logs
from profiles import build_attempts


def recommend_from_file(
    data_dir: str,
    recommender_path: str,
    participant_id: str | None,
    last_n: int | None,
    top_k: int,
) -> pd.DataFrame:
    recommender = joblib.load(recommender_path)
    attempts = build_attempts(load_typing_logs(data_dir))
    if participant_id is not None:
        attempts = attempts[attempts["participant_id"].astype(str) == str(participant_id)]
    if attempts.empty:
        raise ValueError("No attempts found for the requested input.")

    latest_user = attempts.sort_values("attempt_time")["participant_id"].iloc[-1]
    user_attempts = attempts[attempts["participant_id"] == latest_user].sort_values("attempt_time")
    request = user_attempts.rename(columns={"sentence": "target"})[["target", "typed"]]
    return recommender.recommend_from_attempts(request, last_n=last_n, top_k=top_k)


def recommend_from_error_words(
    recommender_path: str,
    error_words: str,
    top_k: int,
) -> pd.DataFrame:
    recommender = joblib.load(recommender_path)
    return recommender.recommend_from_error_words(error_words.split(), top_k=top_k)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Recommend words from a trained trigram recommender.")
    parser.add_argument("--recommender-path", default="artifacts/typing_recommender.joblib")
    parser.add_argument("--data-dir", default=None, help="Typing logs used to build a recent user profile.")
    parser.add_argument("--participant-id", default=None)
    parser.add_argument("--error-words", default=None, help="Space-separated misspelled words to query directly.")
    parser.add_argument("--last-n", type=int, default=20)
    parser.add_argument("--top-k", type=int, default=50)
    parser.add_argument("--output", default=None, help="Optional JSON output path.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.error_words:
        result = recommend_from_error_words(args.recommender_path, args.error_words, args.top_k)
    elif args.data_dir:
        result = recommend_from_file(
            args.data_dir,
            args.recommender_path,
            args.participant_id,
            args.last_n,
            args.top_k,
        )
    else:
        raise ValueError("Pass either --error-words or --data-dir.")

    output = json.dumps(result.to_dict(orient="records"), indent=2)
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
    else:
        print(output)

