import string
from spellchecker import SpellChecker

class FormDiacritic:

    error_name = "FDIA"

    # Mapping from unaccented to possible accented vowels
    ACCENTED_VOWELS = {
        "a": {"à", "â", "ä"},
        "e": {"é", "è", "ê", "ë"},
        "i": {"î", "ï"},
        "o": {"ô", "ö"},
        "u": {"ù", "û", "ü"},
        "c": {"ç"}
    }

    def __init__(self, language="fr", distance=1):
        """
        Initialize the FormDiacritic detector.

        Args:
            language (str): Language code for SpellChecker.
            distance (int): Max number of letters to replace with accented vowels.
        """
        self.spell = SpellChecker(language=language, distance=distance)
        self.distance = distance
        self.punct_table = str.maketrans("", "", string.punctuation)

    def get_error(self, sentence: str):
        """
        Checks if sentence contains any form-diacritic error.
        Returns a tuple: (True, "FDIA") if found, else (False, None)
        """
        words = [w.translate(self.punct_table).lower() for w in sentence.split() if w]
        unknown_words = [w for w in words if w not in self.spell]

        for w in unknown_words:
            if self.is_error(w):
                return True, "FDIA"
        return False, None

    def correct(self, sentence: str) -> str:
        """
        Corrects form-diacritic errors only for unknown words,
        preserving punctuation and casing.
        """
        corrected_words = []

        tokens = sentence.split()
        for word in tokens:
            stripped = word.translate(self.punct_table).lower()
            if stripped and stripped not in self.spell:
                corrected_word = self._fix_word(word)
            else:
                corrected_word = word
            corrected_words.append(corrected_word)

        return " ".join(corrected_words)

    # ---------- internal helper methods ----------

    def is_error(self, word: str) -> bool:
        """
        Returns True if the word can be corrected by replacing up to `distance`
        letters with accented vowels.
        """
        return bool(self._possible_corrections(word))

    def _fix_word(self, word: str) -> str:
        """
        Corrects a single word using form-diacritic substitutions.
        """
        stripped = word.translate(self.punct_table).lower()
        possible = self._possible_corrections(stripped)

        if possible:
            best = max(possible, key=lambda w: self.spell.word_usage_frequency(word=w))
            return word.replace(stripped, best)
        return word

    def _possible_corrections(self, word: str):
        """
        Returns candidates that can be obtained by replacing up to `distance` letters
        in `word` with accented vowels.
        """
        candidates = set()
        
        raw_candidates = self.spell.candidates(word)
        if not raw_candidates:
            return candidates  # empty set instead of None

        for cand in raw_candidates:
            if len(cand) != len(word):
                continue

            diff_count = 0
            for o, c in zip(word, cand):
                if o != c:
                    if o in self.ACCENTED_VOWELS and c in self.ACCENTED_VOWELS[o]:
                        diff_count += 1
                    else:
                        diff_count = self.distance + 1
                        break

            if 0 < diff_count <= self.distance:
                candidates.add(cand)
        return candidates