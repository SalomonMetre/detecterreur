import re
from spellchecker import SpellChecker
from typing import Tuple, Optional
from detecterreur.validator import Validator 

class LetterInsertion:
    """
    Détecte les erreurs d'insertion (lettre en trop).
    Exemple: "commmune" -> "commune"
    """
    error_name = "OINS"
    error_category = "ORTHOGRAPHE"

    def __init__(self, language="fr", distance=1):
        # Initialisation du spellchecker avec la distance spécifiée
        self.spell = SpellChecker(language=language, distance=distance)
        self.distance = distance
        self.validator = Validator()

    def get_error(self, sentence: str) -> Tuple[str, str, bool]:
        # \b\w+\b est idéal : il split par espaces et ponctuation
        words = re.findall(r"\b\w+\b", sentence)
        
        for word in words:
            # 1. On saute si le mot est valide (spaCy ou dictionnaire)
            if self.validator.is_valid(word):
                continue

            # 2. On vérifie si c'est une erreur d'insertion (lettre en trop)
            # On ne vérifie que si le mot est inconnu du dictionnaire pur
            if word.lower() not in self.spell.word_frequency:
                if self._get_correction(word):
                    return self.error_category, self.error_name, True
                    
        return self.error_category, self.error_name, False

    def correct(self, sentence: str) -> str:
        corrected = sentence
        # On itère à l'envers pour ne pas décaler les indices (span) lors des remplacements
        matches = list(re.finditer(r"\b\w+\b", sentence))
        
        for match in reversed(matches):
            word = match.group()
            
            # Sécurité : ne pas corriger un mot valide
            if self.validator.is_valid(word):
                continue
            
            # On cherche une correction uniquement pour les mots inconnus
            if word.lower() not in self.spell.word_frequency:
                fix = self._get_correction(word)
                if fix:
                    start, end = match.span()
                    # Gestion intelligente de la casse
                    if word[0].isupper(): 
                        fix = fix.capitalize()
                    corrected = corrected[:start] + fix + corrected[end:]
                    
        return corrected

    def _get_correction(self, word: str) -> Optional[str]:
        word_lower = word.lower()
        candidates = self.spell.candidates(word_lower)
        if not candidates: return None
        
        valid_candidates = []
        for c in candidates:
            # Règle OINS : Le candidat doit être PLUS COURT (on a inséré une lettre en trop)
            if len(c) >= len(word_lower): 
                continue
            
            # Vérification de la distance et de la sous-séquence
            if (len(word_lower) - len(c)) <= self.distance:
                if self._is_subsequence(c, word_lower):
                    valid_candidates.append(c)

        if not valid_candidates: 
            return None
            
        # On retourne le candidat le plus fréquent dans la langue française
        return max(valid_candidates, key=lambda w: self.spell.word_frequency[w])

    def _is_subsequence(self, sub: str, main: str) -> bool:
        """Vérifie si 'sub' peut être obtenu en supprimant des lettres dans 'main'"""
        it = iter(main)
        return all(char in it for char in sub)