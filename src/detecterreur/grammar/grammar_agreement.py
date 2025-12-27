from typing import Tuple, List
from pygrammalecte import grammalecte_text, GrammalecteGrammarMessage

class GrammarAgreement:
    """
    Detects and corrects French grammatical agreement errors (Gender/Number).
    Focuses on Noun Phrases (gn) and Past Participles (ppas).
    Uses Grammalecte for detection and correction, with strict filtering.

    Category: GRAMMAIRE
    Error: GACC
    """
    error_name = "GACC"
    error_category = "GRAMMAIRE"

    # Only target agreement errors in noun phrases and past participles
    AGREEMENT_TYPES = {"gn", "ppas"}

    def get_error(self, sentence: str) -> Tuple[str, str, bool]:
        """
        Detects agreement errors in the sentence.
        Returns:
            Tuple[str, str, bool]: (error_category, error_name, has_error)
        """
        for message in grammalecte_text(sentence):
            if isinstance(message, GrammalecteGrammarMessage):
                if message.type in self.AGREEMENT_TYPES:
                    return self.error_category, self.error_name, True
        return self.error_category, self.error_name, False

    def correct(self, sentence: str) -> str:
        """
        Corrects agreement errors in the sentence.
        Returns:
            str: The corrected sentence.
        """
        corrected = sentence
        corrections = []

        # Collect all corrections
        for message in grammalecte_text(sentence):
            if isinstance(message, GrammalecteGrammarMessage):
                if message.type in self.AGREEMENT_TYPES and message.suggestions:
                    # Store (start, end, suggestion_list)
                    corrections.append((message.start, message.end, message.suggestions))

        # Apply corrections right-to-left to avoid offset issues
        corrections.sort(key=lambda x: x[0], reverse=True)

        for start, end, suggestions in corrections:
            # Heuristic: Pick the longest suggestion to avoid truncation issues
            # (e.g., "Le fil" vs "La fille")
            best_sugg = max(suggestions, key=len) if suggestions else ""
            corrected = corrected[:start] + best_sugg + corrected[end:]

        return corrected
