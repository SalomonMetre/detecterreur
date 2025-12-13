from pygrammalecte import grammalecte_text, GrammalecteGrammarMessage
from typing import Tuple, Optional

class GrammarAgreement:
    """
    Detects French grammatical agreement errors using pygrammalecte.
    Error code: GACC
    """
    error_name = "GACC"

    AGREEMENT_TYPES = {"conj", "gn", "ppas", "tu", "inte"}

    def get_error(self, sentence: str) -> Tuple[bool, Optional[str]]:
        for message in grammalecte_text(sentence):
            if isinstance(message, GrammalecteGrammarMessage) and message.type in self.AGREEMENT_TYPES:
                return True, "GACC"
        return False, None

    def correct(self, sentence: str) -> str:
        corrected = sentence
        # Apply corrections from last to first to avoid messing up indices
        corrections = []
        for message in grammalecte_text(sentence):
            if isinstance(message, GrammalecteGrammarMessage) and message.type in self.AGREEMENT_TYPES:
                if message.suggestions:
                    corrections.append((message.start, message.end, message.suggestions[0]))
        # sort by start index descending
        corrections.sort(reverse=True, key=lambda x: x[0])
        for start, end, suggestion in corrections:
            corrected = corrected[:start] + suggestion + corrected[end:]
        return corrected
