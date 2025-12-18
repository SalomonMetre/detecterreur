import string
from spellchecker import SpellChecker
import re

class LetterSubstitution:
    error_name = "OSUB"

    def __init__(self, language="fr", distance=1):
        self.spell = SpellChecker(language=language, distance=distance)
        self.distance = distance
        self.punct_table = str.maketrans("", "", string.punctuation)

    def get_error(self, sentence: str):
        words = re.findall(r"\b\w+\b", sentence.lower())
        unknown_words = [w for w in words if w not in self.spell]

        for w in unknown_words:
            if self.is_error(w):
                return True, "LSUB"
        return False, None

    def correct(self, sentence: str) -> str:
        tokens = re.findall(r"[\w']+|[^\s\w]", sentence)
        corrected_words = []

        for word in tokens:
            stripped = word.translate(self.punct_table).lower()
            if stripped and stripped not in self.spell:
                corrected_word = self._fix_word(word)
            else:
                corrected_word = word
            corrected_words.append(corrected_word)

        return " ".join(corrected_words)

    # ---------- internal helper methods ----------

    def is_error(self, word: str) -> bool:
        for candidate in self._safe_candidates(word):
            if len(candidate) != len(word):
                continue
            diff_count = sum(1 for a, b in zip(word, candidate) if a != b)
            if diff_count == 1:
                return True
        return False

    def _fix_word(self, word: str) -> str:
        stripped = word.translate(self.punct_table).lower()
        if not stripped or stripped in self.spell:
            return word

        possible_corrections = [
            c for c in self._safe_candidates(stripped)
            if len(c) == len(stripped) and sum(1 for a, b in zip(stripped, c) if a != b) == 1
        ]

        if possible_corrections:
            best = max(possible_corrections, key=lambda w: self.spell.word_usage_frequency(word=w))
            return word.replace(stripped, best)

        return word

    def _safe_candidates(self, word: str):
        """
        Wrap SpellChecker.candidates to return empty set if None.
        """
        cands = self.spell.candidates(word)
        return cands if cands is not None else set()
