import re
import string
from spellchecker import SpellChecker

class LetterInsertion:
    def __init__(self, language="fr", distance=1):
        """
        Initialize the LetterInsertion detector.

        Args:
            language (str): Language code for SpellChecker.
            distance (int): Max Levenshtein distance to consider for corrections.
                            Recommended 1 for longer words, up to 2 for short words.
        """
        self.spell = SpellChecker(language=language, distance=distance)
        self.distance = distance  # store for reference
        self.punct_table = str.maketrans("", "", string.punctuation)

    def has_insertion_error(self, sentence: str) -> bool:
        """
        Returns True if any unknown word in the sentence contains a letter insertion error,
        ignoring punctuation. Returns False immediately if all words are known.
        """
        # Extract real words ignoring punctuation
        words = re.findall(r"\b\w+\b", sentence.lower())

        # Unknown words only
        unknown_words = [w for w in words if w not in self.spell]
        if not unknown_words:
            return False

        for w in unknown_words:
            if self._is_insertion_error(w):
                return True
        return False

    def correct(self, sentence: str) -> str:
        """
        Corrects letter-insertion errors only for unknown words in the sentence,
        preserving original punctuation and casing.
        """
        corrected_words = []

        # Split sentence into tokens to preserve punctuation
        tokens = re.findall(r"[\w']+|[^\s\w]", sentence)

        for word in tokens:
            stripped = word.translate(self.punct_table).lower()
            if stripped and stripped not in self.spell:
                corrected_word = self._fix_word(word)
            else:
                corrected_word = word
            corrected_words.append(corrected_word)

        # Join back tokens with spaces
        return " ".join(corrected_words)

    # ---------- internal helper methods ----------

    def _is_insertion_error(self, word: str) -> bool:
        """
        Detects if a word likely contains a letter insertion error.
        Uses SpellChecker correction and considers the specified distance.
        """
        if word in self.spell:
            return False
        correction = self.spell.correction(word)
        if not correction:
            return False
        # Consider an insertion error if word length is up to `distance` longer than correction
        return len(word) - len(correction) <= self.distance and len(word) > len(correction)

    def _fix_word(self, word: str) -> str:
        """
        Corrects a single word if unknown, preserving punctuation and casing.
        """
        stripped = word.translate(self.punct_table).lower()
        if not stripped or stripped in self.spell:
            return word
        correction = self.spell.correction(stripped)
        if correction:
            return word.replace(stripped, correction)
        return word
