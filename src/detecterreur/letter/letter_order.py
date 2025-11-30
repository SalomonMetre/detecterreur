import re
import string
from spellchecker import SpellChecker

class LetterOrder:
    def __init__(self, language="fr"):
        """
        Initialize the LetterOrder detector.

        Args:
            language (str): Language code for SpellChecker.
        """
        self.spell = SpellChecker(language=language)
        self.punct_table = str.maketrans("", "", string.punctuation)

    def has_order_error(self, sentence: str) -> bool:
        """
        Returns True if any unknown word in the sentence contains a letter order error
        (two consecutive letters swapped). Ignores punctuation. Returns False immediately
        if all words are known.
        """
        words = re.findall(r"\b\w+\b", sentence.lower())
        unknown_words = [w for w in words if w not in self.spell]

        if not unknown_words:
            return False

        for w in unknown_words:
            if self._is_order_error(w):
                return True
        return False

    def correct(self, sentence: str) -> str:
        """
        Corrects letter order errors for unknown words only,
        preserving original punctuation and casing.
        """
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

    def _is_order_error(self, word: str) -> bool:
        """
        Returns True if the word can be corrected by swapping any two consecutive letters.
        """
        for candidate in self.spell.candidates(word):
            if self._can_be_obtained_by_swapping(word, candidate):
                return True
        return False

    def _fix_word(self, word: str) -> str:
        """
        Corrects a single word with consecutive-letter order error,
        picking the candidate with the highest usage frequency.
        """
        stripped = word.translate(self.punct_table).lower()
        possible_corrections = [
            c for c in self.spell.candidates(stripped)
            if self._can_be_obtained_by_swapping(stripped, c)
        ]

        if possible_corrections:
            best = max(possible_corrections, key=lambda w: self.spell.word_usage_frequency(word=w))
            return word.replace(stripped, best)
        return word

    def _can_be_obtained_by_swapping(self, word: str, candidate: str) -> bool:
        """
        Returns True if candidate can be obtained by swapping any two consecutive letters in word.
        """
        if len(word) != len(candidate):
            return False

        for i in range(len(word) - 1):
            swapped = list(word)
            swapped[i], swapped[i + 1] = swapped[i + 1], swapped[i]
            if "".join(swapped) == candidate:
                return True
        return False