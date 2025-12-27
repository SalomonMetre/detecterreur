import re
from typing import Tuple, Optional
from spellchecker import SpellChecker
from detecterreur.validator import Validator  # <--- IMPORT

class LetterSubstitution:
    error_name = "OSUB"
    error_category = "ORTHOGRAPHE"

    def __init__(self, language: str = "fr", distance: int = 1):
        self.spell = SpellChecker(language=language, distance=distance)
        self.distance = distance
        self.validator = Validator()  # <--- INSTANTIATE

    def get_error(self, sentence: str) -> Tuple[str, str, bool]:
        words = re.findall(r"\b\w+\b", sentence)
        for word in words:
            # SAFETY: If spaCy knows "cuisine", SKIP IT.
            if self.validator.is_valid(word):
                continue
            
            if word.lower() not in self.spell:
                if self._get_substitution_correction(word):
                    return self.error_category, self.error_name, True
        return self.error_category, self.error_name, False

    def correct(self, sentence: str) -> str:
        corrected = sentence
        matches = list(re.finditer(r"\b\w+\b", sentence))

        for match in reversed(matches):
            word = match.group()

            # SAFETY: If spaCy knows "cuisine", SKIP IT.
            if self.validator.is_valid(word):
                continue

            if word.lower() in self.spell:
                continue

            fix = self._get_substitution_correction(word)
            if fix:
                start, end = match.span()
                fix = self._match_case(word, fix)
                corrected = corrected[:start] + fix + corrected[end:]

        return corrected

    def _get_substitution_correction(self, word: str) -> Optional[str]:
        candidates = self.spell.candidates(word)
        if not candidates: return None

        valid_corrections = []
        for candidate in candidates:
            if len(candidate) == len(word):
                diff = sum(1 for a, b in zip(word.lower(), candidate.lower()) if a != b)
                if 1 <= diff <= self.distance:
                    valid_corrections.append(candidate)

        if not valid_corrections: return None
        return max(valid_corrections, key=lambda w: self.spell.word_frequency[w])

    def _match_case(self, original: str, corrected: str) -> str:
        if original.isupper(): return corrected.upper()
        elif original.istitle(): return corrected.capitalize()
        return corrected