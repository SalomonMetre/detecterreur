from pygrammalecte import grammalecte_text, GrammalecteGrammarMessage
from typing import Tuple

class GrammarConjugation:
    """
    Detects French conjugation errors using pygrammalecte.
    Category: GRAMMAIRE
    Error: GCON
    """
    error_name = "GCON"
    error_category = "GRAMMAIRE"

    def __init__(self):
        pass

    # -----------------------------------------------------
    # Public API
    # -----------------------------------------------------
    def get_error(self, sentence: str) -> Tuple[str, str, bool]:
        """
        Returns (error_category, error_name, True/False)
        """
        # Grammalecte returns a generator/list of messages
        for message in grammalecte_text(sentence):
            if isinstance(message, GrammalecteGrammarMessage):
                # Check specifically for conjugation errors
                if message.type == "conj":
                    return self.error_category, self.error_name, True
                    
        return self.error_category, self.error_name, False

    def correct(self, sentence: str) -> str:
        """
        Corrects conjugation errors using pygrammalecte suggestions.
        We apply corrections from Right-to-Left to avoid index shifting issues.
        """
        corrected = sentence
        
        # Collect all conjugation errors
        corrections = []
        for message in grammalecte_text(sentence):
            if isinstance(message, GrammalecteGrammarMessage) and message.type == "conj":
                if message.suggestions:
                    # Store (start, end, replacement)
                    corrections.append((message.start, message.end, message.suggestions[0]))

        # Sort by start index Descending (Right -> Left)
        # This ensures that modifying the end of the string doesn't invalidate 
        # the indices of errors at the beginning.
        corrections.sort(key=lambda x: x[0], reverse=True)

        for start, end, sugg in corrections:
            corrected = corrected[:start] + sugg + corrected[end:]

        return corrected