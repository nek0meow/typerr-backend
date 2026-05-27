from __future__ import annotations

import os

DEFAULT_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000")
DEFAULT_EXPERIMENT_NAME = os.getenv("MLFLOW_EXPERIMENT_NAME", "typing-word-recommendation")
DEFAULT_MODEL_NAME = os.getenv("MLFLOW_MODEL_NAME", "typing-word-recommender")
