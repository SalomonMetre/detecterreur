import re
import string
from typing import Tuple, Optional
from spellchecker import SpellChecker
from detecterreur.validator import Validator  # 1. Import Validator

class LetterOrder:
    """
    Detects and corrects letter order errors (transpositions of adjacent letters).
    Example: "formage" -> "fromage"

    Category: ORTHOGRAPHE
    Error: OORD
    """
    error_name = "OORD"
    error_category = "ORTHOGRAPHE"

    def __init__(self, language: str = "fr"):
        """
        Args:
            language (str): Language for spell checking.
        """
        self.spell = SpellChecker(language=language, distance=1)
        self.punct_table = str.maketrans("", "", string.punctuation)
        self.validator = Validator()  # 2. Instantiate Validator

    def get_error(self, sentence: str) -> Tuple[str, str, bool]:
        """
        Detects letter order errors in the sentence.
        Returns:
            Tuple[str, str, bool]: (error_category, error_name, has_error)
        """
        words = re.findall(r"\b\w+\b", sentence)
        
        for word in words:
            # 3. SAFETY CHECK: If spaCy knows the word, SKIP IT.
            if self.validator.is_valid(word):
                continue
            
            # Check only truly unknown words
            if self.is_error(word):
                return self.error_category, self.error_name, True

        return self.error_category, self.error_name, False

    def correct(self, sentence: str) -> str:
        """
        Corrects letter order errors in the sentence.
        Uses re.finditer to preserve original whitespace and punctuation.
        """
        corrected = sentence
        
        # Iterate in reverse to keep indices valid during replacement
        matches = list(re.finditer(r"\b\w+\b", sentence))
        
        for match in reversed(matches):
            word = match.group()
            
            # 4. SAFETY CHECK during correction too
            if self.validator.is_valid(word):
                continue

            fix = self._get_order_correction(word.lower())
            if fix:
                # Apply case matching
                final_fix = self._match_case(word, fix)
                
                # Replace in string
                start, end = match.span()
                corrected = corrected[:start] + final_fix + corrected[end:]

        return corrected

    def is_error(self, word: str) -> bool:
        """
        Checks if the word contains a letter order error.
        """
        return self._get_order_correction(word.lower()) is not None

    # ---------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------
    def _get_order_correction(self, word: str) -> Optional[str]:
        if not word:
            return None

        candidates = self.spell.candidates(word)
        if not candidates:
            return None

        valid_corrections = []
        for candidate in candidates:
            # Check strict adjacent swap
            if self._can_be_obtained_by_swapping(word, candidate):
                valid_corrections.append(candidate)

        if not valid_corrections:
            return None

        # FIX: Use dictionary access [w] instead of .word_probability(w)
        return max(valid_corrections, key=lambda w: self.spell.word_frequency[w])

    def _can_be_obtained_by_swapping(self, word: str, candidate: str) -> bool:
        """
        Checks if 'candidate' can be obtained by swapping exactly one pair
        of adjacent characters in 'word'.
        """
        if len(word) != len(candidate):
            return False
        
        # Optimization: Words must have exact same character counts (anagram)
        # before we try swapping logic
        if sorted(word) != sorted(candidate):
            return False

        # Try swapping every adjacent pair in 'word'
        word_list = list(word)
        for i in range(len(word_list) - 1):
            # Swap
            word_list[i], word_list[i+1] = word_list[i+1], word_list[i]

            if "".join(word_list) == candidate:
                return True

            # Swap back (backtrack)
            word_list[i], word_list[i+1] = word_list[i+1], word_list[i]

        return False

    def _match_case(self, original: str, corrected: str) -> str:
        """
        Matches the case of the original word to the corrected word.
        """
        if original.isupper():
            return corrected.upper()
        elif original.istitle():
            return corrected.capitalize()
        return corrected