from typing import Optional, Tuple
from pygrammalecte import grammalecte_text, GrammalecteGrammarMessage

class Punctuation:
    """
    Detector and corrector for punctuation errors in French.
    Error code: PUNC

    Uses:
      - pygrammalecte to detect incorrect punctuation (type 'typo')
      - Applies suggestions to fix errors
    """

    def __init__(self):
        self.error_name = "PONC"

    # -----------------------------------------------------
    # Public API
    # -----------------------------------------------------
    def get_error(self, sentence: str) -> Tuple[bool, Optional[str]]:
        """
        Returns (True, 'PUNC') if a punctuation error is detected, else (False, None)
        """
        for message in grammalecte_text(sentence):
            if isinstance(message, GrammalecteGrammarMessage):
                if message.type == "typo":
                    return True, self.error_name
        return False, None

    def correct(self, sentence: str) -> str:
        """
        Applies pygrammalecte suggestions to correct punctuation errors
        while preserving other content.
        """
        corrected = sentence

        for message in grammalecte_text(sentence):
            if isinstance(message, GrammalecteGrammarMessage) and message.type == "typo":
                # Use first suggestion if available
                if message.suggestions:
                    suggestion = message.suggestions[0]
                    # Apply using start/end positions if available
                    if hasattr(message, "start") and hasattr(message, "end"):
                        corrected = corrected[:message.start] + suggestion + corrected[message.end:]
                    else:
                        corrected = corrected.replace(message.message, suggestion, 1)

        return corrected
