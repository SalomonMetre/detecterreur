import string
from spellchecker import SpellChecker

class LetterReplacement:
    def __init__(self, language="fr", distance=1):
        """
        Initialize the LetterReplacement detector.

        Args:
            language (str): Language code for SpellChecker.
            distance (int): Max Levenshtein distance to consider for corrections.
        """
        self.spell = SpellChecker(language=language, distance=distance)
        self.distance = distance
        self.punct_table = str.maketrans("", "", string.punctuation)

    def has_replacement_error(self, sentence: str) -> bool:
        """
        Returns True if any unknown word in the sentence contains a letter replacement error.
        Ignores punctuation. Returns False immediately if all words are known.
        """
        words = [w.translate(self.punct_table).lower() for w in sentence.split() if w]

        unknown_words = [w for w in words if w not in self.spell]
        if not unknown_words:
            return False

        for w in unknown_words:
            if self._is_replacement_error(w):
                return True
        return False

    def correct(self, sentence: str) -> str:
        """
        Corrects letter replacement errors only for unknown words,
        preserving original punctuation and casing.
        """
        corrected_words = []

        for word in sentence.split():
            stripped = word.translate(self.punct_table).lower()
            if stripped and stripped not in self.spell:
                corrected_word = self._fix_word(word)
            else:
                corrected_word = word
            corrected_words.append(corrected_word)

        return " ".join(corrected_words)

    # ---------- internal helper methods ----------

    def _is_replacement_error(self, word: str) -> bool:
        """
        Detects if a word likely contains a letter replacement error.
        """
        for candidate in self.spell.candidates(word):
            if len(candidate) != len(word):
                continue
            # Count positions where letters differ
            diff_count = sum(1 for a, b in zip(word, candidate) if a != b)
            if diff_count == 1:
                return True
        return False

    def _fix_word(self, word: str) -> str:
        """
        Corrects a single word with a letter replacement error using candidate frequencies,
        preserving punctuation and casing.
        """
        stripped = word.translate(self.punct_table).lower()
        if not stripped or stripped in self.spell:
            return word

        possible_corrections = []
        for candidate in self.spell.candidates(stripped):
            if len(candidate) != len(stripped):
                continue
            diff_count = sum(1 for a, b in zip(stripped, candidate) if a != b)
            if diff_count == 1:
                possible_corrections.append(candidate)

        if possible_corrections:
            best = max(possible_corrections, key=lambda w: self.spell.word_usage_frequency(word=w))
            return word.replace(stripped, best)

        return word
