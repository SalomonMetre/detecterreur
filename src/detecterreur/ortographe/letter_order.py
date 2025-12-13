import re
import string
from spellchecker import SpellChecker

class LetterOrder:
    error_name = "LORD"

    def __init__(self, language="fr"):
        self.spell = SpellChecker(language=language)
        self.punct_table = str.maketrans("", "", string.punctuation)

    def get_error(self, sentence: str):
        words = re.findall(r"\b\w+\b", sentence.lower())
        unknown_words = [w for w in words if w not in self.spell]

        for w in unknown_words:
            if self.is_error(w):
                return True, "LORD"
        return False, None

    def correct(self, sentence: str) -> str:
        tokens = re.findall(r"[\w']+|[^\s\w]", sentence)
        corrected_tokens = []

        for word in tokens:
            stripped = word.translate(self.punct_table).lower()
            if stripped and stripped not in self.spell:
                corrected_word = self._fix_word(word)
            else:
                corrected_word = word
            corrected_tokens.append(corrected_word)

        return " ".join(corrected_tokens)

    # ---------- internal helper methods ----------

    def is_error(self, word: str) -> bool:
        for candidate in self._safe_candidates(word):
            if self._can_be_obtained_by_swapping(word, candidate):
                return True
        return False

    def _fix_word(self, word: str) -> str:
        stripped = word.translate(self.punct_table).lower()
        possible_corrections = [
            c for c in self._safe_candidates(stripped)
            if self._can_be_obtained_by_swapping(stripped, c)
        ]

        if possible_corrections:
            best = max(possible_corrections, key=lambda w: self.spell.word_usage_frequency(word=w))
            return word.replace(stripped, best)
        return word

    def _can_be_obtained_by_swapping(self, word: str, candidate: str) -> bool:
        if len(word) != len(candidate):
            return False

        for i in range(len(word) - 1):
            swapped = list(word)
            swapped[i], swapped[i + 1] = swapped[i + 1], swapped[i]
            if "".join(swapped) == candidate:
                return True
        return False

    def _safe_candidates(self, word: str):
        """
        Wrapper around SpellChecker.candidates that returns an empty set
        if SpellChecker returns None.
        """
        cands = self.spell.candidates(word)
        if cands is None:
            return set()
        return cands
