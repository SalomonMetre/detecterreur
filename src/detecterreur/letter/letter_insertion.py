import string
from spellchecker import SpellChecker

class LetterInsertion:
    def __init__(self, language="fr"):
        self.spell = SpellChecker(language=language, distance=1)
        self.punct_table = str.maketrans("", "", string.punctuation)

    def has_insertion_error(self, sentence: str) -> bool:
        """
        Returns True if any word in the sentence contains a letter insertion error,
        ignoring punctuation. If all words are known, returns False.
        """
        words = [w.translate(self.punct_table).lower() for w in sentence.split()]
        if all(w in self.spell for w in words if w):
            return False  # all known words, no insertion error

        for w in words:
            if w and self._is_insertion_error(w):
                return True
        return False

    def correct(self, sentence: str) -> str:
        """
        Corrects all letter-insertion errors in the sentence.
        """
        words = sentence.split()
        corrected_words = [self._fix_word(w) for w in words]
        return " ".join(corrected_words)

    # ---------- internal helper methods ----------

    def _is_insertion_error(self, word: str) -> bool:
        if word in self.spell:
            return False
        correction = self.spell.correction(word)
        if not correction:
            return False
        return len(word) == len(correction) + 1  # one extra letter

    def _fix_word(self, word: str) -> str:
        # strip punctuation temporarily for checking
        stripped = word.translate(self.punct_table).lower()
        if not stripped or stripped in self.spell:
            return word
        correction = self.spell.correction(stripped)
        # preserve original casing and punctuation
        if correction:
            return word.replace(stripped, correction)
        return word
