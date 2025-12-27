import re
from typing import Tuple, Optional
from spellchecker import SpellChecker
from detecterreur.validator import Validator 

class LetterSubstitution:
    """
    Détecte et corrige les erreurs de substitution (une lettre remplacée par une autre).
    Exemple: "vaiture" -> "voiture"
    
    Category: ORTHOGRAPHE
    Error: OSUB
    """
    error_name = "OSUB"
    error_category = "ORTHOGRAPHE"

    def __init__(self, language: str = "fr", distance: int = 1):
        self.spell = SpellChecker(language=language, distance=distance)
        self.distance = distance
        self.validator = Validator()

    def get_error(self, sentence: str) -> Tuple[str, str, bool]:
        """
        Détecte si la phrase contient une erreur de substitution.
        """
        words = re.findall(r"\b\w+\b", sentence)
        for word in words:
            # 1. Sécurité : Si le mot est connu de spaCy ou du dictionnaire, on l'ignore.
            if self.validator.is_valid(word):
                continue
            
            # 2. On ne vérifie que les mots absents du dictionnaire de fréquence
            if word.lower() not in self.spell.word_frequency:
                if self._get_substitution_correction(word):
                    return self.error_category, self.error_name, True
                    
        return self.error_category, self.error_name, False

    def correct(self, sentence: str) -> str:
        """
        Remplace les mots erronés par leur version corrigée.
        """
        corrected = sentence
        matches = list(re.finditer(r"\b\w+\b", sentence))

        # Parcours inversé pour maintenir l'intégrité des indices (spans)
        for match in reversed(matches):
            word = match.group()

            # Sécurité durant la correction
            if self.validator.is_valid(word):
                continue

            # On ignore si le mot minuscule est déjà considéré comme correct
            if word.lower() in self.spell.word_frequency:
                continue

            fix = self._get_substitution_correction(word)
            if fix:
                start, end = match.span()
                fix = self._match_case(word, fix)
                corrected = corrected[:start] + fix + corrected[end:]

        return corrected

    def _get_substitution_correction(self, word: str) -> Optional[str]:
        word_lower = word.lower()
        candidates = self.spell.candidates(word_lower)
        if not candidates: return None

        valid_corrections = []
        for candidate in candidates:
            candidate_lower = candidate.lower()
            # Règle OSUB : La longueur doit être identique à l'original
            if len(candidate_lower) == len(word_lower):
                # On compte le nombre de caractères différents (distance de Hamming)
                diff = sum(1 for a, b in zip(word_lower, candidate_lower) if a != b)
                if 1 <= diff <= self.distance:
                    valid_corrections.append(candidate_lower)

        if not valid_corrections: return None
        
        # On choisit le candidat le plus fréquent
        return max(valid_corrections, key=lambda w: self.spell.word_frequency[w])

    def _match_case(self, original: str, corrected: str) -> str:
        """Applique la casse de l'original au mot corrigé."""
        if original.isupper(): return corrected.upper()
        elif original.istitle(): return corrected.capitalize()
        return corrected