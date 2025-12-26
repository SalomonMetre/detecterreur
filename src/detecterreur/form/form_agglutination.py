import re
import string
from spellchecker import SpellChecker
from typing import Optional, Tuple, List

class FormAgglutination:
    """
    Detector and corrector for French word agglutinations
    (e.g., "dansle" -> "dans le", "silvousplait" -> "s'il vous plaît").
    
    Category: FORME
    Error: FAGL
    """
    error_name = "FAGL"
    error_category = "FORME"

    def __init__(self, language: str = "fr", distance: int = 1):
        self.spell = SpellChecker(language=language, distance=distance)
        self.distance = distance
        self.punct_table = str.maketrans("", "", string.punctuation)

    # -----------------------------
    # Public API
    # -----------------------------
    def get_error(self, sentence: str) -> Tuple[str, str, bool]:
        """
        Returns: (error_category, error_name, True/False)
        """
        # Simple tokenization for detection
        words = re.findall(r"\b\w+\b", sentence.lower())
        
        # Identify unknown words
        unknown_words = [w for w in words if w not in self.spell]

        if not unknown_words:
            return self.error_category, self.error_name, False

        for word in unknown_words:
            if self.is_error(word):
                return self.error_category, self.error_name, True
                
        return self.error_category, self.error_name, False

    def correct(self, sentence: str) -> str:
        """
        Splits agglutinated words into their correct components.
        """
        # Tokenize preserving punctuation
        tokens = re.findall(r"[\w']+|[^\s\w]", sentence)
        corrected_tokens = []

        for token in tokens:
            # Strip punctuation for dictionary check
            stripped = token.translate(self.punct_table).lower()
            
            # If word is valid or empty (just punct), keep it
            if not stripped or stripped in self.spell:
                corrected_tokens.append(token)
                continue

            # Try to fix
            best_multi = self._best_multi_split(stripped)
            
            if best_multi:
                # If we found a split (e.g. "dans le"), use it
                # We assume the user typed lowercase or standard case for agglutinations
                corrected_tokens.append(best_multi)
            else:
                corrected_tokens.append(token)

        return self._rebuild_sentence(corrected_tokens)

    # -----------------------------
    # Core logic
    # -----------------------------
    def is_error(self, word: str) -> bool:
        """
        Returns True if the word can be split into valid sub-words.
        """
        return self._best_multi_split(word) is not None

    # -----------------------------
    # Internal helpers
    # -----------------------------
    def _multi_split_candidates(self, word: str) -> List[str]:
        """
        Generate all valid multi-word splits of `word`.
        Uses recursion with memoization implicitly via the loop structure.
        """
        results = []

        def recurse(start: int, parts: List[str]):
            # Base case: reached end of word
            if start == len(word):
                if len(parts) > 1:
                    results.append(" ".join(parts))
                return

            # Try all possible split points
            for end in range(start + 1, len(word) + 1):
                piece = word[start:end]
                # Only proceed if the piece is a valid word
                if piece in self.spell:
                    recurse(end, parts + [piece])

        recurse(0, [])
        return results

    def _best_multi_split(self, word: str) -> Optional[str]:
        """
        Finds the most likely split based on word frequency.
        """
        candidates = self._multi_split_candidates(word)
        if not candidates:
            return None

        scored = []
        for cand in candidates:
            parts = cand.split()
            # Score = sum of frequencies (simple heuristic)
            # Log-probability would be better mathematically, but this works for basic typos
            freq = sum(self.spell.word_usage_frequency(word=p) for p in parts)
            scored.append((freq, cand))

        # Sort by score descending
        scored.sort(reverse=True, key=lambda x: x[0])
        return scored[0][1]

    def _rebuild_sentence(self, tokens: List[str]) -> str:
        """
        Join tokens and fix punctuation spacing.
        """
        # Initial join with spaces
        text = " ".join(tokens)
        
        # Remove spaces before punctuation (simple rules for French)
        # remove space before . , ) ] }
        text = re.sub(r'\s+([.,)\]}])', r'\1', text)
        
        # fix space after ' (e.g., "l' ami" -> "l'ami")
        text = re.sub(r"(\w')\s+(\w)", r"\1\2", text)
        
        return text