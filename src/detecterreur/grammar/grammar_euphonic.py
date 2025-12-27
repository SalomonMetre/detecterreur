import re
from typing import Tuple

class GrammarEuphonic:
    """
    Detects and corrects missing euphonic markers in French using regex rules.

    Rules:
    1. If a verb ends in a vowel and the subject pronoun starts with a vowel,
       insert "-t-" (e.g., "A il" → "A-t-il", "Parle elle" → "Parle-t-elle").
    2. If a verb ends in 't' or 'd' and is followed by a subject pronoun,
       insert a hyphen (e.g., "Vient il" → "Vient-il", "Prend elle" → "Prend-elle").

    Category: GRAMMAIRE
    Error: GEUF
    """
    error_name = "GEUF"
    error_category = "GRAMMAIRE"

    def __init__(self):
        # Subject pronouns involved in inversion
        self.pronouns = r"(?:il|elle|on|ils|elles|iel)"

        # Vowels (including accented ones common in French verbs)
        self.vowels = "aeiouyàâéèêëîïôùûü"

        # Pattern 1: Vowel collision → Needs "-t-"
        # Example: "A il" → "A-t-il"
        self.pat_vowel = re.compile(
            rf"\b(\w+[{re.escape(self.vowels)}])\s+({self.pronouns})\b",
            re.IGNORECASE
        )

        # Pattern 2: Missing hyphen → Needs "-"
        # Example: "Vient il" → "Vient-il"
        self.pat_consonant = re.compile(
            r"\b(\w+[td])\s+(%s)\b" % self.pronouns,
            re.IGNORECASE
        )

    def get_error(self, sentence: str) -> Tuple[str, str, bool]:
        """
        Detects missing euphonic markers in the sentence.
        Returns:
            Tuple[str, str, bool]: (error_category, error_name, has_error)
        """
        if self.pat_vowel.search(sentence):
            return self.error_category, self.error_name, True
        if self.pat_consonant.search(sentence):
            return self.error_category, self.error_name, True
        return self.error_category, self.error_name, False

    def correct(self, sentence: str) -> str:
        """
        Corrects missing euphonic markers in the sentence.
        Returns:
            str: The corrected sentence.
        """
        corrected = sentence

        # Fix 1: Insert "-t-" for vowel collisions
        corrected = self.pat_vowel.sub(r"\1-t-\2", corrected)

        # Fix 2: Insert "-" for verbs ending in 't' or 'd'
        corrected = self.pat_consonant.sub(r"\1-\2", corrected)

        return corrected
