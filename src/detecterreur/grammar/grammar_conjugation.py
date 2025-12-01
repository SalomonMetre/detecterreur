from pygrammalecte import grammalecte_text, GrammalecteGrammarMessage
from typing import Optional, Tuple

class GrammarConjugation:
    """
    Detects French conjugation errors using pygrammalecte.
    Error code: GCONJ
    """

    def __init__(self):
        self.error_name = "GCONJ"

    # -----------------------------------------------------
    # Public API
    # -----------------------------------------------------
    def get_error(self, sentence: str) -> Tuple[bool, Optional[str]]:
        """
        Returns (True, error_code) if a conjugation error is detected,
        otherwise (False, None).
        """
        for message in grammalecte_text(sentence):
            if isinstance(message, GrammalecteGrammarMessage) and message.type == "conj":
                return True, self.error_name
        return False, None

    def correct(self, sentence: str) -> str:
        """
        Corrects conjugation errors using pygrammalecte suggestions.
        Applies suggestions exactly at the indicated start/end positions.
        """
        corrected = sentence
        offset = 0  # Track offset because replacements can change string length

        for message in grammalecte_text(sentence):
            if isinstance(message, GrammalecteGrammarMessage) and message.type == "conj":
                if message.suggestions:
                    # Take the first suggestion
                    sugg = message.suggestions[0]

                    # Compute real positions accounting for previous replacements
                    start = message.start + offset
                    end = message.end + offset

                    # Apply correction
                    corrected = corrected[:start] + sugg + corrected[end:]

                    # Update offset for next replacements
                    offset += len(sugg) - (end - start)

        return corrected
