from pygrammalecte import grammalecte_text, GrammalecteGrammarMessage
from typing import Tuple, Optional

class GrammarEuphonic:
    """
    Detects euphonics errors in French (type 'tu' in pygrammalecte)
    Reports error code: GEUF
    """

    def __init__(self):
        self.error_name = "GEUF"
        self.pg_type = "tu"  # pygrammalecte error type

    # -----------------------------------------------------
    # Public API
    # -----------------------------------------------------
    def get_error(self, sentence: str) -> Tuple[bool, Optional[str]]:
        """
        Returns True and error code if a euphonics error is detected.
        """
        for message in grammalecte_text(sentence):
            if isinstance(message, GrammalecteGrammarMessage):
                if message.type == self.pg_type:
                    return True, self.error_name
        return False, None

    def correct(self, sentence: str) -> str:
        """
        Applies pygrammalecte suggestions to fix euphonics errors.
        """
        corrected = sentence
        offset = 0  # track shift in character positions after replacements

        for message in grammalecte_text(sentence):
            if isinstance(message, GrammalecteGrammarMessage) and message.type == self.pg_type:
                if message.suggestions:
                    start = message.start + offset
                    end = message.end + offset
                    # Apply first suggestion
                    replacement = message.suggestions[0]
                    corrected = corrected[:start] + replacement + corrected[end:]
                    offset += len(replacement) - (end - start)

        return corrected
