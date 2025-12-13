import re
import string
from spellchecker import SpellChecker
from typing import Optional, Tuple, List


class FormAgglutination:
    """
    Detector and corrector for French word agglutinations
    (e.g., "dansle" → "dans le", "silvousplait" → "s'il vous plaît").

    Uses:
      - pyspellchecker for fast dictionary lookups and frequency data
    """
    error_name = "FAGL"

    def __init__(self, language: str = "fr", distance: int = 1):
        self.spell = SpellChecker(language=language, distance=distance)
        self.distance = distance
        self.punct_table = str.maketrans("", "", string.punctuation)
        self.error_name = "FAGL"  # Forme Agglutinée

    # -----------------------------
    # Public API
    # -----------------------------
    def get_error(self, sentence: str) -> Tuple[bool, Optional[str]]:
        words = re.findall(r"\b\w+\b", sentence.lower())
        unknown_words = [w for w in words if w not in self.spell]

        if not unknown_words:
            return False, None

        for word in unknown_words:
            if self.is_error(word):
                return True, self.error_name
        return False, None

    def correct(self, sentence: str) -> str:
        # Tokenize while keeping punctuation separate
        tokens = re.findall(r"[\w']+|[^\s\w]", sentence)
        corrected_tokens = []

        for token in tokens:
            stripped = token.translate(self.punct_table).lower()
            if not stripped or stripped in self.spell:
                corrected_tokens.append(token)
                continue

            fixed = self._fix_word(token, stripped)
            corrected_tokens.append(fixed)

        # Rebuild sentence with spaces
        return self._rebuild_sentence(corrected_tokens, sentence)

    # -----------------------------
    # Core logic
    # -----------------------------
    def is_error(self, word: str) -> bool:
        # Detect if a multi-word split exists
        if self._best_multi_split(word):
            return True
        return False

    # -----------------------------
    # Internal helpers
    # -----------------------------
    def _multi_split_candidates(self, word: str) -> List[str]:
        """
        Generate all possible multi-word splits of `word`.
        Example:
            'silvousplait' => ['s il vous plait', 'si l vous plait', ...]
        """
        results = []

        def recurse(start: int, parts: List[str]):
            if start == len(word):
                if len(parts) > 1:
                    results.append(" ".join(parts))
                return

            for end in range(start + 1, len(word) + 1):
                piece = word[start:end]
                if piece in self.spell:
                    recurse(end, parts + [piece])

        recurse(0, [])
        return results

    def _best_multi_split(self, word: str) -> Optional[str]:
        candidates = self._multi_split_candidates(word)
        if not candidates:
            return None

        scored = []
        for cand in candidates:
            parts = cand.split()
            freq = sum(self.spell.word_usage_frequency(word=p) for p in parts)
            scored.append((freq, cand))

        scored.sort(reverse=True, key=lambda x: x[0])
        return scored[0][1]

    def _fix_word(self, original_token: str, lowered_stripped: str) -> str:
        best_multi = self._best_multi_split(lowered_stripped)
        if best_multi:
            return original_token.replace(lowered_stripped, best_multi, 1)
        return original_token

    def _rebuild_sentence(self, tokens: List[str], original_sentence: str) -> str:
        """
        Rebuild the sentence preserving spacing similar to the original.
        """
        rebuilt = []
        i = 0
        for tok in tokens:
            if i > 0:
                # Add space if previous char in original was space
                rebuilt.append(' ')
            rebuilt.append(tok)
            i += 1
        return ''.join(rebuilt)
