from pygrammalecte import grammalecte_text, GrammalecteGrammarMessage
from typing import Tuple

class GrammarAgreement:
    """
    Detects French grammatical agreement errors (Gender/Number).
    Focuses on Noun Phrases (gn) and Past Participles (ppas).
    Category: GRAMMAIRE
    Error: GACC
    """
    error_name = "GACC"
    error_category = "GRAMMAIRE"
    
    # Exclude 'conj' (verbs) and 'tu' (euphonics)
    AGREEMENT_TYPES = {"gn", "ppas"}

    def get_error(self, sentence: str) -> Tuple[str, str, bool]:
        for message in grammalecte_text(sentence):
            if isinstance(message, GrammalecteGrammarMessage):
                if message.type in self.AGREEMENT_TYPES:
                    return self.error_category, self.error_name, True
        return self.error_category, self.error_name, False

    def correct(self, sentence: str) -> str:
        corrected = sentence
        corrections = []

        for message in grammalecte_text(sentence):
            if isinstance(message, GrammalecteGrammarMessage):
                if message.type in self.AGREEMENT_TYPES:
                    if message.suggestions:
                        # Store (start, end, suggestion_list)
                        corrections.append((message.start, message.end, message.suggestions))

        # Apply Right-to-Left
        corrections.sort(key=lambda x: x[0], reverse=True)

        for start, end, suggestions in corrections:
            # Heuristic: If we have multiple suggestions, pick the longest one 
            # (Often avoids "Le fil" vs "La fille" truncation issues)
            # OR just pick the first one [0]
            best_sugg = suggestions[0] 
            corrected = corrected[:start] + best_sugg + corrected[end:]

        return corrected