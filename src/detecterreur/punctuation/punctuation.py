import re
from typing import Tuple

class Punctuation:
    """
    Detects and corrects punctuation spacing errors in French using Regex.

    Rules enforced:
    1. High punctuation (:;?!) must have a space BEFORE them.
    2. Low punctuation (.,) must NOT have a space BEFORE them.
    3. All punctuation (.,:;?!) must have a space AFTER them (if followed by a word).

    Category: PONCTUATION
    Error: PONC
    """
    error_name = "PONC"
    error_category = "PONCTUATION"

    def __init__(self):
        # Pattern 1: Missing space before high punctuation (!?;:)
        # Matches alphanumeric char followed immediately by punctuation
        self.pat_missing_space_before = re.compile(
            r'(?<=[a-zA-Z0-9à-üÀ-Ü])([:;?!])'
        )

        # Pattern 2: Extra space before low punctuation (.,)
        # Matches whitespace followed by . or ,
        self.pat_extra_space_before = re.compile(
            r'\s+([.,])'
        )

        # Pattern 3: Missing space after punctuation
        # Matches punctuation followed immediately by a letter (start of next word)
        # Excludes numbers to protect decimals (e.g., 1.5)
        self.pat_missing_space_after = re.compile(
            r'([.,:;?!])(?=[a-zA-Zà-üÀ-Ü])'
        )

    def get_error(self, sentence: str) -> Tuple[str, str, bool]:
        """
        Detects punctuation spacing errors in the sentence.
        Returns:
            Tuple[str, str, bool]: (error_category, error_name, has_error)
        """
        if (self.pat_missing_space_before.search(sentence) or
            self.pat_extra_space_before.search(sentence) or
            self.pat_missing_space_after.search(sentence)):
            return self.error_category, self.error_name, True

        return self.error_category, self.error_name, False

    def correct(self, sentence: str) -> str:
        """
        Corrects punctuation spacing errors in the sentence.
        Returns:
            str: The corrected sentence.
        """
        corrected = sentence

        # 1. Remove space before . or ,
        # Example: "Bonjour , monde" → "Bonjour, monde"
        corrected = self.pat_extra_space_before.sub(r'\1', corrected)

        # 2. Add space before : ; ? !
        # Example: "Bonjour!" → "Bonjour !"
        corrected = self.pat_missing_space_before.sub(r' \1', corrected)

        # 3. Add space after punctuation if followed by a letter
        # Example: "Bonjour.Salut" → "Bonjour. Salut"
        corrected = self.pat_missing_space_after.sub(r'\1 ', corrected)

        return corrected
