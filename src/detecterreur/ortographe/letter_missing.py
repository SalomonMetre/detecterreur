import re
import string
from spellchecker import SpellChecker

class LetterMissing:
    error_name = "OMIS"

    def __init__(self, language="fr", distance=1):
        self.spell = SpellChecker(language=language, distance=distance)
        self.distance = distance
        self.punct_table = str.maketrans("", "", string.punctuation)

    def get_error(self, sentence: str):
        words = re.findall(r"\b\w+\b", sentence.lower())
        unknown_words = [w for w in words if w not in self.spell]

        for w in unknown_words:
            if self.is_error(w):
                return True, "LMIS"
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

    # ---------- internal helpers ----------

    def is_error(self, word: str) -> bool:
        for candidate in self._safe_candidates(word):
            if len(candidate) == len(word) + 1:
                for i in range(len(candidate)):
                    if candidate[:i] + candidate[i+1:] == word:
                        return True
        return False

    def _fix_word(self, word: str) -> str:
        stripped = word.translate(self.punct_table).lower()
        if not stripped or stripped in self.spell:
            return word

        possible_corrections = []
        for candidate in self._safe_candidates(stripped):
            if len(candidate) == len(stripped) + 1:
                for i in range(len(candidate)):
                    if candidate[:i] + candidate[i+1:] == stripped:
                        possible_corrections.append(candidate)
                        break

        if possible_corrections:
            best = max(possible_corrections, key=lambda w: self.spell.word_usage_frequency(word=w))
            return word.replace(stripped, best)

        return word

    def _safe_candidates(self, word: str):
        """
        Wraps SpellChecker.candidates to return empty set if None.
        """
        cands = self.spell.candidates(word)
        return cands if cands is not None else set()
