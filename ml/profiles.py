from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher

import pandas as pd

from text_processing import extract_missed_words, trigram_document


GROUP_COLUMNS = ["PARTICIPANT_ID", "TEST_SECTION_ID"]
BACKSPACE_KEYS = {"BKSP", "BACKSPACE"}
IGNORED_KEYS = {
    "SHIFT",
    "CAPS_LOCK",
    "CTRL",
    "CONTROL",
    "ALT",
    "TAB",
    "ENTER",
    "ESC",
    "ESCAPE",
}
MAX_RECONSTRUCTION_STATES = 100
BACKSPACE_REPEAT_MS = 80.0


@dataclass
class ReconstructionResult:
    typed: str
    distance_to_recorded: int | None
    status: str


def _edit_distance(left: str, right: str) -> int:
    previous = list(range(len(right) + 1))
    for left_index, left_char in enumerate(left, start=1):
        current = [left_index]
        for right_index, right_char in enumerate(right, start=1):
            current.append(
                min(
                    previous[right_index] + 1,
                    current[right_index - 1] + 1,
                    previous[right_index - 1] + (left_char != right_char),
                )
            )
        previous = current
    return previous[-1]


def _candidate_score(candidate: str, recorded: str) -> tuple[float, int]:
    prefix = recorded[: max(len(candidate) + 8, min(len(recorded), len(candidate)))]
    return (1.0 - SequenceMatcher(a=candidate, b=prefix, autojunk=False).ratio(), abs(len(candidate) - len(prefix)))


def _estimated_backspace_counts(row: pd.Series, has_recorded_input: bool) -> range:
    if not has_recorded_input:
        return range(1, 2)

    duration = max(float(row["RELEASE_TIME"]) - float(row["PRESS_TIME"]), 0.0)
    if duration < 250:
        return range(1, 2)

    max_count = min(20, max(1, round(duration / BACKSPACE_REPEAT_MS)))
    return range(1, max_count + 1)


def reconstruct_typed_text(group: pd.DataFrame, recorded_input: str | None = None) -> ReconstructionResult:
    """Rebuild final typed text from keystrokes, applying repeated/held backspaces."""
    states = {""}
    has_recorded_input = bool(recorded_input)

    for _, row in group.sort_values(["PRESS_TIME", "KEYSTROKE_ID"]).iterrows():
        letter = str(row["LETTER"])
        keycode = int(row["KEYCODE"])
        normalized_letter = letter.upper()

        if keycode == 8 or normalized_letter in BACKSPACE_KEYS:
            next_states: set[str] = set()
            for state in states:
                for count in _estimated_backspace_counts(row, has_recorded_input):
                    next_states.add(state[:-count] if count < len(state) else "")
            states = next_states or {""}
            if recorded_input and len(states) > MAX_RECONSTRUCTION_STATES:
                states = set(
                    sorted(states, key=lambda candidate: _candidate_score(candidate, recorded_input))[
                        :MAX_RECONSTRUCTION_STATES
                    ]
                )
            continue

        if normalized_letter in IGNORED_KEYS:
            continue

        if len(letter) == 1:
            states = {state + letter for state in states}

    if not states:
        return ReconstructionResult(typed=recorded_input or "", distance_to_recorded=None, status="empty")

    if not recorded_input:
        return ReconstructionResult(typed=next(iter(states)), distance_to_recorded=None, status="reconstructed")

    typed = min(states, key=lambda candidate: _edit_distance(candidate, recorded_input))
    distance = _edit_distance(typed, recorded_input)
    fallback_threshold = max(3, round(len(recorded_input) * 0.25))
    if distance > fallback_threshold:
        return ReconstructionResult(
            typed=recorded_input,
            distance_to_recorded=distance,
            status="recorded_input_fallback",
        )
    if distance > 0:
        return ReconstructionResult(
            typed=typed,
            distance_to_recorded=distance,
            status="held_backspace_deduced",
        )
    return ReconstructionResult(typed=typed, distance_to_recorded=0, status="reconstructed_exact")


def build_attempts(raw: pd.DataFrame) -> pd.DataFrame:
    """Collapse keystroke rows into one row per user typing attempt."""
    rows: list[dict[str, object]] = []

    for (participant_id, section_id), group in raw.groupby(GROUP_COLUMNS, sort=False):
        group = group.sort_values(["PRESS_TIME", "KEYSTROKE_ID"])
        sentence = str(group["SENTENCE"].iloc[0])
        recorded_input = str(group["USER_INPUT"].iloc[0])
        reconstruction = reconstruct_typed_text(group, recorded_input=recorded_input)
        typed = reconstruction.typed or recorded_input
        missed_words = extract_missed_words(sentence, typed)

        rows.append(
            {
                "participant_id": participant_id,
                "test_section_id": section_id,
                "attempt_time": float(group["PRESS_TIME"].min()),
                "sentence": sentence,
                "typed": typed,
                "recorded_user_input": recorded_input,
                "reconstruction_status": reconstruction.status,
                "reconstruction_distance": reconstruction.distance_to_recorded,
                "missed_words": missed_words,
                "error_trigrams": trigram_document(missed_words),
            }
        )

    return pd.DataFrame(rows)


def build_user_error_profiles(raw: pd.DataFrame, last_n: int | None = None) -> pd.DataFrame:
    """Build one TF-IDF-ready trigram document per user from recent attempts."""
    attempts = build_attempts(raw)
    attempts = attempts.sort_values(["participant_id", "attempt_time"])
    if last_n is not None and last_n > 0:
        attempts = attempts.groupby("participant_id", group_keys=False).tail(last_n)

    rows: list[dict[str, object]] = []
    for participant_id, group in attempts.groupby("participant_id", sort=False):
        missed_words: list[str] = []
        for words in group["missed_words"]:
            missed_words.extend(words)

        trigram_doc = trigram_document(missed_words)
        if not trigram_doc:
            continue

        rows.append(
            {
                "participant_id": participant_id,
                "attempt_count": int(len(group)),
                "missed_word_count": int(len(missed_words)),
                "missed_words": " ".join(missed_words),
                "error_trigrams": trigram_doc,
            }
        )

    if not rows:
        raise ValueError("No misspelled words with at least 3 letters were found.")
    return pd.DataFrame(rows)
