from pygrammalecte import grammalecte_text, GrammalecteGrammarMessage
from typing import Tuple

class Punctuation:
    """
    Detector and corrector for punctuation errors in French.
    Handles typography rules (spaces before ?, !, :, ; and quotes).
    
    Category: PONCTUATION
    Error: PONC
    """
    error_name = "PONC"
    error_category = "PONCTUATION"

    # Grammalecte categorizes punctuation/typography errors as "typo"
    ERROR_TYPE = "typo"

    def __init__(self):
        pass

    # -----------------------------------------------------
    # Public API
    # -----------------------------------------------------
    def get_error(self, sentence: str) -> Tuple[str, str, bool]:
        """
        Returns: (error_category, error_name, True/False)
        """
        for message in grammalecte_text(sentence):
            if isinstance(message, GrammalecteGrammarMessage):
                if message.type == self.ERROR_TYPE:
                    return self.error_category, self.error_name, True
                    
        return self.error_category, self.error_name, False

    def correct(self, sentence: str) -> str:
        """
        Applies Grammalecte suggestions to fix punctuation errors.
        Uses Right-to-Left application to preserve string indices.
        """
        corrected = sentence
        corrections = []

        # 1. Collect all corrections
        for message in grammalecte_text(sentence):
            if isinstance(message, GrammalecteGrammarMessage):
                if message.type == self.ERROR_TYPE:
                    if message.suggestions:
                        # Store (start, end, replacement)
                        corrections.append((message.start, message.end, message.suggestions[0]))

        # 2. Sort by start index Descending (Right -> Left)
        corrections.sort(key=lambda x: x[0], reverse=True)

        # 3. Apply corrections
        for start, end, replacement in corrections:
            corrected = corrected[:start] + replacement + corrected[end:]

        return corrected