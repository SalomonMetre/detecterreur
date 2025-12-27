from typing import Tuple, List
from pygrammalecte import grammalecte_text, GrammalecteGrammarMessage

class GrammarConjugation:
    """
    Detects and corrects French conjugation errors using Grammalecte.
    Only targets errors of type "conj" (conjugation).
    Applies corrections right-to-left to avoid index shifting issues.

    Category: GRAMMAIRE
    Error: GCON
    """
    error_name = "GCON"
    error_category = "GRAMMAIRE"

    def get_error(self, sentence: str) -> Tuple[str, str, bool]:
        """
        Detects conjugation errors in the sentence.
        Returns:
            Tuple[str, str, bool]: (error_category, error_name, has_error)
        """
        for message in grammalecte_text(sentence):
            if isinstance(message, GrammalecteGrammarMessage):
                if message.type == "conj":
                    return self.error_category, self.error_name, True
        return self.error_category, self.error_name, False

    def correct(self, sentence: str) -> str:
        """
        Corrects conjugation errors in the sentence.
        Returns:
            str: The corrected sentence.
        """
        corrected = sentence
        corrections = []

        # Collect all conjugation errors and their suggested corrections
        for message in grammalecte_text(sentence):
            if isinstance(message, GrammalecteGrammarMessage) and message.type == "conj":
                if message.suggestions:
                    corrections.append((message.start, message.end, message.suggestions[0]))

        # Apply corrections right-to-left to avoid index shifting issues
        corrections.sort(key=lambda x: x[0], reverse=True)

        for start, end, suggestion in corrections:
            corrected = corrected[:start] + suggestion + corrected[end:]

        return corrected
