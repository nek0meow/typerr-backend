from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import mlflow
import mlflow.pyfunc
import pandas as pd
from mlflow.models.signature import infer_signature

from config import DEFAULT_EXPERIMENT_NAME, DEFAULT_MODEL_NAME, DEFAULT_TRACKING_URI
from data_loader import load_typing_logs
from profiles import build_user_error_profiles
from recommender import TypingErrorRecommender, load_vocabulary
from mlflow_model import TypingRecommendationModel


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_VOCABULARY_PATH = BASE_DIR.parent / "src" / "main" / "resources" / "static" / "20k"


def train(
    data_dir: str,
    vocabulary_path: str,
    tracking_uri: str,
    experiment_name: str,
    registered_model_name: str | None,
    output_dir: str | None,
    last_n: int | None,
    top_k: int,
) -> dict[str, object]:
    raw = load_typing_logs(data_dir)
    profiles = build_user_error_profiles(raw, last_n=last_n)
    vocabulary = load_vocabulary(vocabulary_path)

    recommender = TypingErrorRecommender()
    recommender.fit(profiles, vocabulary)

    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(experiment_name)

    with mlflow.start_run(run_name="typing-trigram-recommender") as run:
        output = Path(output_dir or "artifacts")
        output.mkdir(parents=True, exist_ok=True)
        recommender_path = output / "typing_recommender.joblib"
        model_info_path = output / "model_info.json"
        sample_recommendations_path = output / "sample_recommendations.csv"

        joblib.dump(recommender, recommender_path)

        sample_words = profiles["missed_words"].iloc[0].split()
        sample_recommendations = recommender.recommend_from_error_words(sample_words, top_k=top_k)
        sample_recommendations.to_csv(sample_recommendations_path, index=False)

        metrics = {
            "raw_rows": len(raw),
            "trained_users": len(profiles),
            "vocabulary_words": len(vocabulary),
            "indexed_words": len(recommender.word_index),
            "trigram_features": len(recommender.vectorizer.vocabulary_),
            "avg_missed_words_per_user": float(profiles["missed_word_count"].mean()),
        }
        params = {
            "data_dir": str(data_dir),
            "vocabulary_path": str(vocabulary_path),
            "last_n": last_n or 0,
            "top_k": top_k,
            "model_type": "tfidf-trigram-recommender",
        }

        mlflow.log_params(params)
        mlflow.log_metrics(metrics)
        mlflow.log_artifact(str(sample_recommendations_path))
        input_example = pd.DataFrame(
            {
                "target": ["example target sentence"],
                "typed": ["example traget sentence"],
                "top_k": [10],
                "last_n": [last_n or 0],
            }
        )
        signature = infer_signature(
            input_example,
            sample_recommendations.head(1),
        )

        mlflow.pyfunc.log_model(
            name="model",
            python_model=TypingRecommendationModel(),
            artifacts={"recommender": str(recommender_path)},
            code_paths=[str(BASE_DIR / "recommender.py"), str(BASE_DIR / "text_processing.py")],
            registered_model_name=registered_model_name,
            input_example=input_example,
            signature=signature,
        )

        model_uri = f"runs:/{run.info.run_id}/model"
        result = {
            "run_id": run.info.run_id,
            "model_uri": model_uri,
            "registered_model_name": registered_model_name,
            "tracking_uri": tracking_uri,
            "metrics": metrics,
        }
        model_info_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        mlflow.log_artifact(str(model_info_path))

    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train a TF-IDF trigram typing-word recommender.")
    parser.add_argument("--data-dir", required=True, help="File or directory with sample_file-like typing logs.")
    parser.add_argument(
        "--vocabulary-path",
        default=str(DEFAULT_VOCABULARY_PATH),
        help="Word list used to build final recommendations.",
    )
    parser.add_argument("--tracking-uri", default=DEFAULT_TRACKING_URI)
    parser.add_argument("--experiment-name", default=DEFAULT_EXPERIMENT_NAME)
    parser.add_argument("--registered-model-name", default=DEFAULT_MODEL_NAME)
    parser.add_argument("--output-dir", default="artifacts")
    parser.add_argument("--last-n", type=int, default=None, help="Use only the last N attempts per user.")
    parser.add_argument("--top-k", type=int, default=50, help="Number of sample recommendations to write.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    training_result = train(
        data_dir=args.data_dir,
        vocabulary_path=args.vocabulary_path,
        tracking_uri=args.tracking_uri,
        experiment_name=args.experiment_name,
        registered_model_name=args.registered_model_name,
        output_dir=args.output_dir,
        last_n=args.last_n,
        top_k=args.top_k,
    )
    print(json.dumps(training_result, indent=2))
