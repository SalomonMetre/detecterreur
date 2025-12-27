import re
from spellchecker import SpellChecker
from typing import Tuple, Optional

class FormAgglutination:
    """
    Detects and corrects agglutination (two words stuck together).
    
    Robust Logic:
    1. If word is in dictionary -> IGNORE (it's valid).
    2. If word is unknown -> Try split.
    3. Split is accepted ONLY if:
       - Both parts are valid words.
       - AND at least one part is a "Glue Word" (Preposition, Pronoun, Article).
    
    Category: FORME
    Error: FAGL
    """
    error_name = "FAGL"
    error_category = "FORME"

    def __init__(self):
        self.spell = SpellChecker(language='fr')
        
        # Comprehensive list of "Glue Words" (High frequency grammatical connectors)
        # These are the usual suspects in agglutination errors.
        self.glue_words = {
            # Articles / Determiners
            "le", "la", "les", "l", "un", "une", "des", "du", "de", "d", "au", "aux",
            "ce", "cet", "cette", "ces", "ma", "ta", "sa", "mes", "tes", "ses", 
            "mon", "ton", "son", "notre", "votre", "leur", "nos", "vos", "leurs",
            # Pronouns
            "je", "tu", "il", "elle", "on", "nous", "vous", "ils", "elles", 
            "me", "te", "se", "y", "en", "lui", "moi", "toi", "soi", "qui", "que",
            # Prepositions / Conjunctions
            "a", "à", "et", "ou", "où", "si", "ni", "car", "par", "pour", "sans", 
            "dans", "sur", "sous", "vers", "avec", "chez", "mais", "donc", "or"
        }

    def get_error(self, sentence: str) -> Tuple[str, str, bool]:
        words = re.findall(r"\b\w+\b", sentence)
        for word in words:
            if self._check_word(word):
                return self.error_category, self.error_name, True
        return self.error_category, self.error_name, False

    def correct(self, sentence: str) -> str:
        corrected = sentence
        # Use finditer to preserve whitespace/punctuation
        matches = list(re.finditer(r"\b\w+\b", sentence))
        
        # Reverse iteration to modify indices safely
        for match in reversed(matches):
            word = match.group()
            
            # Check for split
            split = self._check_word(word)
            if split:
                start, end = match.span()
                corrected = corrected[:start] + split + corrected[end:]
        
        return corrected

    def _check_word(self, word: str) -> Optional[str]:
        """
        Returns 'word1 word2' if safe split found, else None.
        """
        # 1. Quick Valid Check
        # If the word is known, assume it's correct.
        # This protects "mangent" (known) from becoming "man gent" (man=slang, gent=noun).
        if word.lower() in self.spell:
            return None
        
        # 2. Try Splitting
        length = len(word)
        if length < 3: return None

        for i in range(1, length):
            left = word[:i]
            right = word[i:]
            
            # Optimization: Single letters must be 'y', 'a' or 'l', 'd' (elisions usually handled elsewhere, but safe to check)
            if len(left) == 1 and left.lower() not in ["y", "a", "à", "l", "d"]: continue
            if len(right) == 1 and right.lower() not in ["y", "a", "à"]: continue

            # 3. GLUE CHECK (The Safety Filter)
            # One of the parts MUST be a glue word.
            # "dansle" -> "dans" (Glue) + "le" (Glue) -> OK.
            # "mangent" -> "man" (Not Glue) + "gent" (Not Glue) -> REJECT.
            is_glue = (left.lower() in self.glue_words or right.lower() in self.glue_words)
            if not is_glue:
                continue

            # 4. DICTIONARY CHECK
            # Both parts must be valid words.
            if self._is_valid(left) and self._is_valid(right):
                return f"{left} {right}"
        
        return None

    def _is_valid(self, w: str) -> bool:
        # Helper to check validity
        return w.lower() in self.glue_words or w.lower() in self.spell