import re
import string
from spellchecker import SpellChecker

class LetterOrder:
    
    error_name = "OORD"
    error_category = "ORTHOGRAPHE"

    def __init__(self, language="fr", distance=1):
        """
        Detects letter order errors (transpositions of adjacent letters).
        Example: "formage" -> "fromage"
        """
        self.spell = SpellChecker(language=language, distance=distance)
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
        best_candidate = self._get_order_correction(word)
        return best_candidate is not None

    def correct(self, sentence: str) -> str:
        tokens = re.findall(r"[\w']+|[^\s\w]", sentence)
        corrected = []

        for token in tokens:
            stripped = token.translate(self.punct_table).lower()
            
            if stripped and stripped not in self.spell:
                fix = self._get_order_correction(stripped)
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
    def _get_order_correction(self, word: str):
        if not word:
            return None
            
        candidates = self.spell.candidates(word)
        if not candidates:
            return None

        valid_corrections = []
        for c in candidates:
            # We are looking for candidates obtained by swapping TWO CONSECUTIVE letters
            if self._can_be_obtained_by_swapping(word, c):
                valid_corrections.append(c)
        
        if not valid_corrections:
            return None

        # Pick the most frequent valid correction
        best_word = max(valid_corrections, key=lambda w: self.spell.word_frequency[w])
        return best_word

    def _can_be_obtained_by_swapping(self, word: str, candidate: str) -> bool:
        """
        Returns True if 'candidate' can be obtained by swapping exactly one pair
        of adjacent characters in 'word'.
        """
        if len(word) != len(candidate):
            return False

        # Try swapping every adjacent pair in 'word' to see if it matches 'candidate'
        word_list = list(word)
        for i in range(len(word_list) - 1):
            # Swap
            word_list[i], word_list[i+1] = word_list[i+1], word_list[i]
            
            if "".join(word_list) == candidate:
                return True
            
            # Swap back (backtrack) to check the next pair
            word_list[i], word_list[i+1] = word_list[i+1], word_list[i]
            
        return False