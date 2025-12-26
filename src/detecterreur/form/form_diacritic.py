import re
import string
from spellchecker import SpellChecker

class FormDiacritic:
    
    error_name = "FDIA"
    error_category = "FORME"

    # Equivalence classes: characters that can be swapped for one another in a diacritic error
    BASE_MAP = {
        'a': 'a', 'à': 'a', 'â': 'a', 'ä': 'a',
        'e': 'e', 'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
        'i': 'i', 'î': 'i', 'ï': 'i',
        'o': 'o', 'ô': 'o', 'ö': 'o',
        'u': 'u', 'ù': 'u', 'û': 'u', 'ü': 'u',
        'c': 'c', 'ç': 'c'
    }

    def __init__(self, language="fr", distance=1):
        self.spell = SpellChecker(language=language, distance=distance)
        self.distance = distance
        self.punct_table = str.maketrans("", "", string.punctuation)

    def get_error(self, sentence: str):
        """
        Returns: (error_category, error_name, True/False)
        """
        # Improved tokenization: split on apostrophes and non-word chars
        words = re.findall(r"\b\w+\b", sentence.lower())
        
        for w in words:
            if self.is_error(w):
                return self.error_category, self.error_name, True
                
        return self.error_category, self.error_name, False

    def correct(self, sentence: str) -> str:
        # 1. Tokenize: Split on spaces but keep punctuation/apostrophes as separate tokens if needed
        # Regex explanation: Match words OR apostrophes/punctuation OR spaces
        tokens = re.findall(r"\w+|[^\w\s]|\s+", sentence)
        corrected_tokens = []

        for token in tokens:
            # Skip spaces/punctuation
            if not token.strip() or not token[0].isalnum():
                corrected_tokens.append(token)
                continue

            # Attempt correction
            corrected_word = self._fix_word(token)
            corrected_tokens.append(corrected_word)

        return "".join(corrected_tokens)

    # ---------- Internal Logic ----------

    def is_error(self, word: str) -> bool:
        """
        Returns True if a 'better' diacritic version exists, 
        OR if the word is unknown and a diacritic version exists.
        """
        # If word is unknown, and we have a correction -> Error
        if word not in self.spell:
            return bool(self._possible_corrections(word))
        
        # If word IS known (like "ete"), check if a diacritic sibling is MUCH more frequent
        # This catches "ete" -> "été" while ignoring "cote" -> "côté" (context dependent)
        siblings = self._possible_corrections(word)
        if not siblings: 
            return False
            
        current_freq = self.spell.word_usage_frequency(word)
        best_sibling = max(siblings, key=lambda w: self.spell.word_usage_frequency(word=w))
        best_freq = self.spell.word_usage_frequency(best_sibling)
        
        # Heuristic: If the sibling is significantly more frequent (e.g. 50x), treat current as error
        # "ete" freq is very low compared to "été"
        if best_sibling != word and best_freq > (current_freq * 10):
            return True
            
        return False

    def _fix_word(self, original_word: str) -> str:
        lower_word = original_word.translate(self.punct_table).lower()
        possible = self._possible_corrections(lower_word)

        if possible:
            # Pick most frequent candidate
            best_candidate = max(possible, key=lambda w: self.spell.word_usage_frequency(word=w))
            
            # If the original was already in the list (valid word), 
            # we only swap if the best candidate is significantly better (frequency check)
            if lower_word in self.spell:
                current_freq = self.spell.word_usage_frequency(lower_word)
                best_freq = self.spell.word_usage_frequency(best_candidate)
                # Only swap known words if frequency diff is huge
                if best_freq < (current_freq * 10):
                    return original_word

            return self._match_case(original_word, best_candidate)

        return original_word

    def _possible_corrections(self, word: str):
        """
        Returns valid candidates where differences are purely diacritic
        and within the allowed edit distance.
        """
        candidates = set()
        
        # Force generation of candidates even if word is known
        # We merge distance 1 and 2 (if configured)
        raw_candidates = self.spell.edit_distance_1(word)
        if self.distance > 1:
            raw_candidates.update(self.spell.edit_distance_2(word))
            
        # Add the word itself if it's in the dict, so we can compare frequencies later
        if word in self.spell:
            raw_candidates.add(word)

        for cand in raw_candidates:
            # Filter: Must be in dictionary AND be a diacritic sibling
            if cand in self.spell and self._are_diacritic_siblings(word, cand):
                candidates.add(cand)
                
        return candidates

    def _are_diacritic_siblings(self, word1: str, word2: str) -> bool:
        if len(word1) != len(word2):
            return False

        diff_count = 0
        for c1, c2 in zip(word1, word2):
            if c1 != c2:
                base1 = self.BASE_MAP.get(c1, c1)
                base2 = self.BASE_MAP.get(c2, c2)
                if base1 != base2: return False
                diff_count += 1

        return 0 <= diff_count <= self.distance # Allow 0 for frequency comparison

    def _match_case(self, original: str, corrected: str) -> str:
        if original.isupper(): return corrected.upper()
        elif original.istitle(): return corrected.capitalize()
        return corrected