import re
import string
from spellchecker import SpellChecker

class LetterSubstitution:
    
    error_name = "OSUB"
    error_category = "ORTHOGRAPHE"

    def __init__(self, language="fr", distance=1):
        """
        Detects letter substitution errors (wrong letter used).
        Example: "teléphone" -> "téléphone" (e -> é)
                 "water" -> "later" (w -> l)
        
        Args:
            distance (int): Max number of substituted characters allowed.
        """
        self.spell = SpellChecker(language=language, distance=distance)
        self.distance = distance
        self.punct_table = str.maketrans("", "", string.punctuation)

    def get_error(self, sentence: str):
        """
        Returns: (error_category, error_name, True/False)
        """
        words = re.findall(r"\b\w+\b", sentence.lower())
        unknown = [w for w in words if w not in self.spell]

        if not unknown:
            return self.error_category, self.error_name, False

        for w in unknown:
            if self.is_error(w):
                return self.error_category, self.error_name, True
                
        return self.error_category, self.error_name, False

    def is_error(self, word: str) -> bool:
        best_candidate = self._get_substitution_correction(word)
        return best_candidate is not None

    def correct(self, sentence: str) -> str:
        tokens = re.findall(r"[\w']+|[^\s\w]", sentence)
        corrected = []

        for token in tokens:
            stripped = token.translate(self.punct_table).lower()
            
            if stripped and stripped not in self.spell:
                fix = self._get_substitution_correction(stripped)
                if fix:
                    corrected.append(fix)
                else:
                    corrected.append(token)
            else:
                corrected.append(token)

        return " ".join(corrected)

    # ---------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------
    def _get_substitution_correction(self, word: str):
        if not word:
            return None
            
        candidates = self.spell.candidates(word)
        if not candidates:
            return None

        valid_corrections = []
        for c in candidates:
            # Substitution must preserve length
            if len(c) != len(word):
                continue

            # Count differences (Hamming distance)
            diff_count = sum(1 for a, b in zip(word, c) if a != b)
            
            # Must be at least 1 diff, but not more than allowed distance
            if 1 <= diff_count <= self.distance:
                valid_corrections.append(c)

        if not valid_corrections:
            return None

        # Pick the most frequent valid correction
        best_word = max(valid_corrections, key=lambda w: self.spell.word_frequency[w])
        return best_word