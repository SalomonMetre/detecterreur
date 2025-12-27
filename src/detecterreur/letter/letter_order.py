import re
import string
from typing import Tuple, Optional
from spellchecker import SpellChecker
from detecterreur.validator import Validator 

class LetterOrder:
    """
    Détecte et corrige les erreurs d'ordre des lettres (transpositions adjacentes).
    Exemple: "formage" -> "fromage"

    Category: ORTHOGRAPHE
    Error: OORD
    """
    error_name = "OORD"
    error_category = "ORTHOGRAPHE"

    def __init__(self, language: str = "fr"):
        # On garde une distance de 1 car une inversion correspond à un Edit Distance de 1 (Damerau-Levenshtein)
        self.spell = SpellChecker(language=language, distance=1)
        self.validator = Validator()

    def get_error(self, sentence: str) -> Tuple[str, str, bool]:
        """
        Détecte si la phrase contient une inversion de lettres adjacentes.
        """
        words = re.findall(r"\b\w+\b", sentence)
        
        for word in words:
            # 1. Sécurité : On ignore le mot s'il est connu par spaCy ou pyspellchecker
            if self.validator.is_valid(word):
                continue
            
            # 2. Vérification de l'erreur d'ordre
            if self.is_error(word):
                return self.error_category, self.error_name, True

        return self.error_category, self.error_name, False

    def correct(self, sentence: str) -> str:
        """
        Corrige les inversions en préservant la ponctuation et les espaces.
        """
        corrected = sentence
        matches = list(re.finditer(r"\b\w+\b", sentence))
        
        # Parcours inversé pour garder les indices de span valides
        for match in reversed(matches):
            word = match.group()
            
            # Sécurité durant la correction
            if self.validator.is_valid(word):
                continue

            # On vérifie si le mot en minuscule a une correction par inversion
            fix = self._get_order_correction(word.lower())
            if fix:
                final_fix = self._match_case(word, fix)
                start, end = match.span()
                corrected = corrected[:start] + final_fix + corrected[end:]

        return corrected

    def is_error(self, word: str) -> bool:
        """
        Vérifie si le mot est une erreur de type inversion.
        """
        return self._get_order_correction(word.lower()) is not None

    # ---------------------------------------------------------
    # Helpers Internes
    # ---------------------------------------------------------
    def _get_order_correction(self, word: str) -> Optional[str]:
        if not word:
            return None

        candidates = self.spell.candidates(word)
        if not candidates:
            return None

        valid_corrections = []
        for candidate in candidates:
            # Règle OORD : Doit être obtenu par un swap de lettres adjacentes
            if self._can_be_obtained_by_swapping(word, candidate):
                valid_corrections.append(candidate)

        if not valid_corrections:
            return None

        # Sélection du mot le plus probable selon la fréquence d'usage
        return max(valid_corrections, key=lambda w: self.spell.word_frequency[w])

    def _can_be_obtained_by_swapping(self, word: str, candidate: str) -> bool:
        """
        Vérifie si 'candidate' est le résultat de l'inversion d'exactement
        une paire de lettres adjacentes dans 'word'.
        """
        if len(word) != len(candidate):
            return False
        
        # Test rapide : doivent être des anagrammes parfaits
        if sorted(word) != sorted(candidate):
            return False

        # On simule les swaps adjacents
        word_list = list(word)
        for i in range(len(word_list) - 1):
            # Swap i et i+1
            word_list[i], word_list[i+1] = word_list[i+1], word_list[i]
            if "".join(word_list) == candidate:
                return True
            # Backtrack (remise en place pour le prochain test)
            word_list[i], word_list[i+1] = word_list[i+1], word_list[i]

        return False

    def _match_case(self, original: str, corrected: str) -> str:
        """
        Applique la casse de l'original au mot corrigé.
        """
        if original.isupper():
            return corrected.upper()
        elif original.istitle():
            return corrected.capitalize()
        return corrected