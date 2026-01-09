import re
import string
from typing import Tuple, Optional
from spellchecker import SpellChecker
from detecterreur.validator import Validator 

class LetterMissing:
    """
    Détecte et corrige les erreurs d'omission (lettre manquante).
    Exemple: "commne" -> "commune" (Manque le 'u')

    Category: ORTHOGRAPHE
    Error: OMIS
    """
    error_name = "OMAN"
    error_category = "ORTHOGRAPHE"

    def __init__(self, language: str = "fr", distance: int = 1):
        self.spell = SpellChecker(language=language, distance=distance)
        self.distance = distance
        self.validator = Validator()

    def get_error(self, sentence: str) -> Tuple[str, str, bool]:
        """
        Détecte si la phrase contient un mot avec une lettre manquante.
        """
        # On extrait uniquement les mots (lettres/chiffres), ignorant la ponctuation
        words = re.findall(r"\b\w+\b", sentence)
        
        for word in words:
            # 1. Sécurité : Si spaCy ou pyspellchecker connaissent le mot, on l'ignore
            if self.validator.is_valid(word):
                continue

            # 2. On vérifie si c'est une omission
            if self.is_error(word):
                return self.error_category, self.error_name, True

        return self.error_category, self.error_name, False

    def correct(self, sentence: str) -> str:
        """
        Corrige les omissions en préservant la structure originale.
        """
        corrected = sentence
        matches = list(re.finditer(r"\b\w+\b", sentence))
        
        # Inversion pour préserver les indices de remplacement
        for match in reversed(matches):
            word = match.group()
            lower_word = word.lower()

            # Sécurité durant la correction
            if self.validator.is_valid(word):
                continue
            
            # Si le mot (en minuscule) est dans le dictionnaire, on ne touche à rien
            if lower_word in self.spell.word_frequency:
                continue

            fix = self._get_missing_correction(lower_word)
            if fix:
                final_fix = self._match_case(word, fix)
                start, end = match.span()
                corrected = corrected[:start] + final_fix + corrected[end:]

        return corrected

    def is_error(self, word: str) -> bool:
        """
        Vérifie si le mot présente une erreur d'omission.
        """
        return self._get_missing_correction(word.lower()) is not None

    # ---------------------------------------------------------
    # Helpers Internes
    # ---------------------------------------------------------
    def _get_missing_correction(self, word: str) -> Optional[str]:
        if not word:
            return None

        candidates = self.spell.candidates(word)
        if not candidates:
            return None

        valid_corrections = []
        for candidate in candidates:
            # Règle OMIS : Le candidat est PLUS LONG (on a oublié une lettre)
            if len(candidate) > len(word):
                diff = len(candidate) - len(word)
                if diff <= self.distance:
                    # Sous-séquence : "commne" est contenu dans "commune"
                    if self._is_subsequence(word, candidate):
                        valid_corrections.append(candidate)

        if not valid_corrections:
            return None

        # On choisit le mot le plus fréquent dans la langue française
        return max(valid_corrections, key=lambda w: self.spell.word_frequency[w])
    
    def _is_subsequence(self, sub: str, main: str) -> bool:
        """
        Vérifie si 'sub' peut être formé en supprimant des lettres dans 'main'.
        """
        it = iter(main)
        return all(char in it for char in sub)

    def _match_case(self, original: str, corrected: str) -> str:
        """
        Applique la casse du mot original au mot corrigé.
        """
        if original.isupper():
            return corrected.upper()
        elif original.istitle():
            return corrected.capitalize()
        return corrected