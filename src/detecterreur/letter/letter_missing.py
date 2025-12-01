import re
import string
from spellchecker import SpellChecker

class LetterMissing:
    def __init__(self, language="fr", distance=1):
        """
        Initialize the LetterMissing detector.

        Args:
            language (str): Language code for SpellChecker.
            distance (int): Max Levenshtein distance to consider for corrections.
        """
        self.spell = SpellChecker(language=language, distance=distance)
        self.distance = distance
        self.punct_table = str.maketrans("", "", string.punctuation)

    def get_error(self, sentence: str):
        """
        Returns a tuple (has_error, error_type).
        True and "LMIS" if a missing-letter error is found, otherwise False, None.
        """
        words = re.findall(r"\b\w+\b", sentence.lower())

        unknown_words = [w for w in words if w not in self.spell]
        if not unknown_words:
            return False, None

        for w in unknown_words:
            if self.is_error(w):
                return True, "LMIS"
        return False, None

    def correct(self, sentence: str) -> str:
        """
        Corrects missing letter errors only for unknown words,
        preserving original punctuation and casing.
        """
        corrected_words = []

        tokens = re.findall(r"[\w']+|[^\s\w]", sentence)

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
        """
        Detects if a word likely has a missing letter
        by checking if any candidate can be obtained by adding a single letter.
        """
        for candidate in self.spell.candidates(word):
            if len(candidate) == len(word) + 1:
                for i in range(len(candidate)):
                    if candidate[:i] + candidate[i+1:] == word:
                        return True
        return False

    def _fix_word(self, word: str) -> str:
        """
        Corrects a single word with missing letters using candidate frequencies,
        preserving punctuation and casing.
        """
        stripped = word.translate(self.punct_table).lower()
        if not stripped or stripped in self.spell:
            return word

        possible_corrections = []
        for candidate in self.spell.candidates(stripped):
            if len(candidate) == len(stripped) + 1:
                for i in range(len(candidate)):
                    if candidate[:i] + candidate[i+1:] == stripped:
                        possible_corrections.append(candidate)
                        break

        if possible_corrections:
            best = max(possible_corrections, key=lambda w: self.spell.word_usage_frequency(word=w))
            return word.replace(stripped, best)

        return word
