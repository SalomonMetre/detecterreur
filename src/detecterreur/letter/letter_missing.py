import re
import string
from typing import Tuple, Optional
from spellchecker import SpellChecker
from detecterreur.validator import Validator  # 1. Import Validator

class LetterMissing:
    """
    Detects and corrects missing letter errors (omissions) in French words.
    Example: "commne" -> "commune" (Missing 'u')

    Category: ORTHOGRAPHE
    Error: OMIS
    """
    error_name = "OMIS"
    error_category = "ORTHOGRAPHE"

    def __init__(self, language: str = "fr", distance: int = 1):
        """
        Args:
            language (str): Language for spell checking.
            distance (int): Max number of missing characters allowed.
        """
        self.spell = SpellChecker(language=language, distance=distance)
        self.distance = distance
        self.punct_table = str.maketrans("", "", string.punctuation)
        self.validator = Validator()  # 2. Instantiate Validator

    def get_error(self, sentence: str) -> Tuple[str, str, bool]:
        """
        Detects missing letter errors in the sentence.
        Returns:
            Tuple[str, str, bool]: (error_category, error_name, has_error)
        """
        words = re.findall(r"\b\w+\b", sentence)
        
        for word in words:
            # 3. SAFETY CHECK: If spaCy knows the word, SKIP IT.
            if self.validator.is_valid(word):
                continue

            # Check only unknown words
            if self.is_error(word):
                return self.error_category, self.error_name, True

        return self.error_category, self.error_name, False

    def correct(self, sentence: str) -> str:
        """
        Corrects missing letter errors in the sentence.
        Uses re.finditer to preserve original whitespace and punctuation.
        """
        corrected = sentence
        
        # Iterate in reverse to keep indices valid during replacement
        matches = list(re.finditer(r"\b\w+\b", sentence))
        
        for match in reversed(matches):
            word = match.group()
            lower_word = word.lower()

            # 4. SAFETY CHECK during correction too
            if self.validator.is_valid(word):
                continue
            
            # Additional check for pyspellchecker's own dictionary
            if lower_word in self.spell:
                continue

            fix = self._get_missing_correction(lower_word)
            if fix:
                # Apply case matching
                final_fix = self._match_case(word, fix)
                
                # Replace in string
                start, end = match.span()
                corrected = corrected[:start] + final_fix + corrected[end:]

        return corrected

    def is_error(self, word: str) -> bool:
        """
        Checks if the word contains a missing letter error.
        """
        # Ensure we check the lower case version
        return self._get_missing_correction(word.lower()) is not None

    # ---------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------
    def _get_missing_correction(self, word: str) -> Optional[str]:
        if not word:
            return None

        candidates = self.spell.candidates(word)
        if not candidates:
            return None

        valid_corrections = []
        for candidate in candidates:
            # OMIS Rule: Candidate must be LONGER than word (we add to word to fix)
            if len(candidate) > len(word):
                diff = len(candidate) - len(word)
                if diff <= self.distance:
                    # Subsequence check: "commne" is subseq of "commune"
                    if self._is_subsequence(word, candidate):
                        valid_corrections.append(candidate)

        if not valid_corrections:
            return None

        # FIX: Use dictionary access [w] instead of .word_probability(w)
        return max(valid_corrections, key=lambda w: self.spell.word_frequency[w])
    
    def _is_subsequence(self, sub: str, main: str) -> bool:
        """
        Checks if 'sub' can be formed by deleting characters from 'main'.
        Example: sub="commne", main="commune" -> True
        """
        it = iter(main)
        return all(char in it for char in sub)

    def _match_case(self, original: str, corrected: str) -> str:
        """
        Matches the case of the original word to the corrected word.
        """
        if original.isupper():
            return corrected.upper()
        elif original.istitle():
            return corrected.capitalize()
        return corrected