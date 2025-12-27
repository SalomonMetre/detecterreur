import re
from spellchecker import SpellChecker
from typing import Tuple, Optional
from detecterreur.validator import Validator # <--- IMPORT

class FormDiacritic:
    error_name = "FDIA"
    error_category = "FORME"

    def __init__(self, distance: int = 1):
        self.spell = SpellChecker(language='fr', distance=distance)
        self.validator = Validator() # <--- INSTANTIATE

    def get_error(self, sentence: str) -> Tuple[str, str, bool]:
        words = re.findall(r"\b\w+\b", sentence)
        for word in words:
            # SAFETY: "cuisine" is valid -> Skip
            if self.validator.is_valid(word):
                continue
                
            if self._get_correction(word):
                return self.error_category, self.error_name, True
        return self.error_category, self.error_name, False

    def correct(self, sentence: str) -> str:
        corrected = sentence
        matches = list(re.finditer(r"\b\w+\b", sentence))
        
        for match in reversed(matches):
            word = match.group()
            
            # SAFETY: "cuisine" is valid -> Skip
            if self.validator.is_valid(word):
                continue

            fix = self._get_correction(word)
            if fix:
                start, end = match.span()
                fix = self._match_case(word, fix)
                corrected = corrected[:start] + fix + corrected[end:]
        return corrected

    def _get_correction(self, word: str) -> Optional[str]:
        candidates = self.spell.candidates(word)
        if not candidates: return None

        import unicodedata
        def remove_accents(input_str):
            nfkd_form = unicodedata.normalize('NFKD', input_str)
            return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

        word_stripped = remove_accents(word.lower())
        valid_candidates = []
        for c in candidates:
            if c != word.lower() and remove_accents(c) == word_stripped:
                valid_candidates.append(c)

        if not valid_candidates: return None
        return max(valid_candidates, key=lambda w: self.spell.word_frequency[w])

    def _match_case(self, original: str, corrected: str) -> str:
        if original.isupper(): return corrected.upper()
        elif original.istitle(): return corrected.capitalize()
        return corrected