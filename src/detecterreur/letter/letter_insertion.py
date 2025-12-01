import re
import string
from spellchecker import SpellChecker

class LetterInsertion:
    
    error_name = "LINS"

    def __init__(self, language="fr", distance=1):
        """
        Detects insertion-type spelling errors (extra unnecessary letters).

        Args:
            language (str): Language code for SpellChecker.
            distance (int): Max Levenshtein distance for correction.
        """
        self.spell = SpellChecker(language=language, distance=distance)
        self.distance = distance
        self.punct_table = str.maketrans("", "", string.punctuation)

    # ---------------------------------------------------------
    # NEW API
    # ---------------------------------------------------------
    def get_error(self, sentence: str):
        """
        Returns:
            (True, "LINS") if an insertion error is found.
            (False, None) otherwise.
        """
        words = re.findall(r"\b\w+\b", sentence.lower())
        unknown = [w for w in words if w not in self.spell]

        if not unknown:
            return False, None

        for w in unknown:
            if self.is_error(w):
                return True, "LINS"

        return False, None

    def is_error(self, word: str) -> bool:
        """
        Determines whether a word contains a likely letter insertion error.
        """
        if word in self.spell:
            return False

        correction = self.spell.correction(word)
        if not correction:
            return False

        # insertion = word longer than correction by <= distance
        return (
            len(word) > len(correction)
            and len(word) - len(correction) <= self.distance
        )

    # ---------------------------------------------------------
    # Correction function unchanged
    # ---------------------------------------------------------
    def correct(self, sentence: str) -> str:
        """
        Corrects only insertion errors, preserving punctuation and casing.
        """
        tokens = re.findall(r"[\w']+|[^\s\w]", sentence)
        corrected = []

        for token in tokens:
            stripped = token.translate(self.punct_table).lower()

            if stripped and stripped not in self.spell:
                fixed = self._fix_word(token)
            else:
                fixed = token

            corrected.append(fixed)

        return " ".join(corrected)

    # ---------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------
    def _fix_word(self, word: str) -> str:
        stripped = word.translate(self.punct_table).lower()

        if not stripped or stripped in self.spell:
            return word

        correction = self.spell.correction(stripped)
        if correction:
            return word.replace(stripped, correction)

        return word
