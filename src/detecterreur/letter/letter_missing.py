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

    def has_missing_letter_error(self, sentence: str) -> bool:
        """
        Returns True if any unknown word in the sentence contains a missing letter error.
        Ignores punctuation. Returns False immediately if all words are known.
        """
        words = re.findall(r"\b\w+\b", sentence.lower())  # extract "real" words

        # Unknown words only
        unknown_words = [w for w in words if w not in self.spell]
        if not unknown_words:
            return False

        for w in unknown_words:
            if self._is_missing_letter(w):
                return True
        return False

    def correct(self, sentence: str) -> str:
        """
        Corrects missing letter errors only for unknown words,
        preserving original punctuation and casing.
        """
        corrected_words = []

        # Split sentence by whitespace, keep punctuation attached
        tokens = re.findall(r"[\w']+|[^\s\w]", sentence)

        for word in tokens:
            stripped = word.translate(self.punct_table).lower()
            if stripped and stripped not in self.spell:
                corrected_word = self._fix_word(word)
            else:
                corrected_word = word
            corrected_words.append(corrected_word)

        # Join back preserving original spacing as best as possible
        return " ".join(corrected_words)

    # ---------- internal helper methods ----------

    def _is_missing_letter(self, word: str) -> bool:
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

        # Candidates that can be obtained by adding one letter
        possible_corrections = []
        for candidate in self.spell.candidates(stripped):
            if len(candidate) == len(stripped) + 1:
                for i in range(len(candidate)):
                    if candidate[:i] + candidate[i+1:] == stripped:
                        possible_corrections.append(candidate)
                        break

        if possible_corrections:
            # pick the candidate with the highest usage frequency
            best = max(possible_corrections, key=lambda w: self.spell.word_usage_frequency(word=w))
            return word.replace(stripped, best)

        return word
