import re
import string
from spellchecker import SpellChecker

class LetterInsertion:
    
    error_name = "OINS"
    error_category = "ORTHOGRAPHE"

    def __init__(self, language="fr", distance=1):
        """
        Detects insertion-type spelling errors (extra unnecessary letters).
        Args:
            distance (int): Max number of extra characters allowed.
                            If distance=2, 'commmune' -> 'commune' (1 del) is valid.
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

        # Fix: Ensure we always return 3 values
        if not unknown:
            return self.error_category, self.error_name, False

        for w in unknown:
            if self.is_error(w):
                return self.error_category, self.error_name, True

        return self.error_category, self.error_name, False

    def is_error(self, word: str) -> bool:
        best_candidate = self._get_insertion_correction(word)
        return best_candidate is not None

    def correct(self, sentence: str) -> str:
        tokens = re.findall(r"[\w']+|[^\s\w]", sentence)
        corrected = []

        for token in tokens:
            stripped = token.translate(self.punct_table).lower()

            if stripped and stripped not in self.spell:
                fix = self._get_insertion_correction(stripped)
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
    def _get_insertion_correction(self, word: str):
        if not word: 
            return None

        candidates = self.spell.candidates(word)
        if not candidates:
            return None

        valid_corrections = []
        for c in candidates:
            # 1. Candidate must be shorter (we are looking for insertion errors in the original)
            if len(word) > len(c):
                # 2. The difference in length must be <= allowed distance
                diff = len(word) - len(c)
                if diff <= self.distance:
                    # 3. Candidate must be a subsequence (only deletions allowed)
                    if self._is_subsequence(sub=c, main=word):
                        valid_corrections.append(c)

        if not valid_corrections:
            return None

        # Pick the most frequent valid correction
        best_word = max(valid_corrections, key=lambda w: self.spell.word_frequency[w])
        return best_word

    def _is_subsequence(self, sub: str, main: str) -> bool:
        """
        Returns True if 'sub' can be formed by deleting 0 or more characters from 'main'.
        Example: sub='bana', main='banana' -> True
        """
        it = iter(main)
        # Check if every char in 'sub' is found in 'main' in the correct order
        return all(char in it for char in sub)