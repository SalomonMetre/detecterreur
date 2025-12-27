import re
from spellchecker import SpellChecker
from typing import Tuple, Optional
from detecterreur.validator import Validator  # 1. Import Validator

class LetterInsertion:
    """
    Detects insertion errors (extra letter).
    Example: "commmune" -> "commune"
    Category: ORTHOGRAPHE, Error: OINS
    """
    error_name = "OINS"
    error_category = "ORTHOGRAPHE"

    def __init__(self, language="fr", distance=1):
        self.spell = SpellChecker(language=language, distance=distance)
        self.distance = distance
        self.validator = Validator()  # 2. Instantiate Validator

    def get_error(self, sentence: str) -> Tuple[str, str, bool]:
        words = re.findall(r"\b\w+\b", sentence)
        for word in words:
            # 3. SAFETY CHECK: If spaCy knows the word, SKIP IT.
            if self.validator.is_valid(word):
                continue

            # Only check truly unknown words
            if word.lower() not in self.spell and self._get_correction(word):
                return self.error_category, self.error_name, True
        return self.error_category, self.error_name, False

    def correct(self, sentence: str) -> str:
        corrected = sentence
        matches = list(re.finditer(r"\b\w+\b", sentence))
        
        for match in reversed(matches):
            word = match.group()
            
            # 4. SAFETY CHECK during correction too
            if self.validator.is_valid(word):
                continue
            
            if word.lower() in self.spell: 
                continue
            
            fix = self._get_correction(word)
            if fix:
                start, end = match.span()
                if word[0].isupper(): fix = fix.capitalize()
                corrected = corrected[:start] + fix + corrected[end:]
        return corrected

    def _get_correction(self, word: str) -> Optional[str]:
        candidates = self.spell.candidates(word)
        if not candidates: return None
        
        valid = []
        for c in candidates:
            # OINS Rule: Candidate must be SHORTER than word (we delete from word to fix)
            if len(c) >= len(word): continue
            
            diff = len(word) - len(c)
            if diff <= self.distance:
                # Subsequence check: "commune" is subseq of "commmune"
                if self._is_subsequence(c, word):
                    valid.append(c)

        if not valid: return None
        # FIX: Use dictionary access
        return max(valid, key=lambda w: self.spell.word_frequency[w])

    def _is_subsequence(self, sub: str, main: str) -> bool:
        it = iter(main)
        return all(char in it for char in sub)