from __future__ import annotations

import json

import joblib
import mlflow.pyfunc
import pandas as pd


class TypingRecommendationModel(mlflow.pyfunc.PythonModel):
    def load_context(self, context: mlflow.pyfunc.PythonModelContext) -> None:
        self.recommender = joblib.load(context.artifacts["recommender"])

    @staticmethod
    def _as_dataframe(model_input: object) -> pd.DataFrame:
        if isinstance(model_input, pd.DataFrame):
            return model_input
        if isinstance(model_input, dict):
            return pd.DataFrame(model_input)
        if isinstance(model_input, list):
            return pd.DataFrame(model_input)
        return pd.DataFrame([model_input])

    def predict(self, context, model_input):
        model_input = self._as_dataframe(model_input)
        top_k = int(model_input["top_k"].iloc[0]) if "top_k" in model_input else 50
        last_n = int(model_input["last_n"].iloc[0]) if "last_n" in model_input else None

        if "error_words" in model_input:
            words: list[str] = []
            for value in model_input["error_words"].dropna():
                if isinstance(value, list):
                    words.extend(value)
                else:
                    words.extend(str(value).split())
            result = self.recommender.recommend_from_error_words(words, top_k=top_k)
        else:
            attempts = model_input.rename(columns={"sentence": "target", "user_input": "typed"})
            result = self.recommender.recommend_from_attempts(
                attempts[["target", "typed"]],
                last_n=last_n,
                top_k=top_k,
            )

        output = result.copy()
        output["matched_trigrams"] = output["matched_trigrams"].apply(
            lambda value: json.dumps(str(value).split())
        )
        return output
