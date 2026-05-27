from __future__ import annotations

import re
from collections import Counter
from difflib import SequenceMatcher


WORD_PATTERN = re.compile(r"[a-z]+")


def normalize_words(text: object, min_length: int = 3) -> list[str]:
    """Split text into lowercase english words, treating every other symbol as space."""
    words = WORD_PATTERN.findall(str(text).lower())
    return [word for word in words if len(word) >= min_length]


def word_trigrams(word: str) -> list[str]:
    """Return character trigrams for one normalized word."""
    if len(word) < 3:
        return []
    return [word[index : index + 3] for index in range(len(word) - 2)]


def trigrams_for_words(words: list[str]) -> list[str]:
    trigrams: list[str] = []
    for word in words:
        trigrams.extend(word_trigrams(word))
    return trigrams


def trigram_document(words: list[str]) -> str:
    return " ".join(trigrams_for_words(words))


def trigram_counts(words: list[str]) -> Counter[str]:
    return Counter(trigrams_for_words(words))


def extract_missed_words(target: object, typed: object) -> list[str]:
    """Return target words that were replaced or deleted in user input."""
    target_words = normalize_words(target)
    typed_words = normalize_words(typed)
    missed: list[str] = []
    matcher = SequenceMatcher(a=target_words, b=typed_words, autojunk=False)

    for tag, i1, i2, _j1, _j2 in matcher.get_opcodes():
        if tag in {"replace", "delete"}:
            missed.extend(target_words[i1:i2])

    return missed

