import re
from typing import Tuple, Optional
from pygrammalecte import grammalecte_text, GrammalecteGrammarMessage

class FormCase:
    """
    Detects capitalization errors at sentence starts or after punctuation,
    using regex and pygrammalecte.

    Error code: FMAJ
    """
    error_name = "FMAJ"

    def __init__(self):
        # regex to find words following sentence boundaries (start or after ., !, ?)
        self.sentence_start_pattern = re.compile(r'(^|[.!?]\s+)(\w)')

    # -------------------------------
    # Public API
    # -------------------------------

    def get_error(self, sentence: str) -> Tuple[bool, Optional[str]]:
        """
        Returns (True, "FMAJ") if a capitalization error is detected,
        otherwise (False, None)
        """
        for message in grammalecte_text(sentence):
            if isinstance(message, GrammalecteGrammarMessage):
                if message.type == "maj":
                    return True, "FMAJ"

        # Regex fallback
        for match in self.sentence_start_pattern.finditer(sentence):
            letter = match.group(2)
            if letter.islower():
                return True, "FMAJ"

        return False, None

    def correct(self, sentence: str) -> str:
        """
        Corrects capitalization errors using pygrammalecte suggestions if available,
        otherwise uses regex capitalization for sentence starts.
        """
        corrected = sentence

        # Apply pygrammalecte suggestions for "maj" errors
        for message in grammalecte_text(corrected):
            if isinstance(message, GrammalecteGrammarMessage) and message.type == "maj":
                # Use first suggestion from suggestions list if available
                if message.suggestions:
                    suggestion = message.suggestions[0]
                    corrected = corrected[:message.start] + suggestion + corrected[message.end:]

        # Regex fallback for sentence starts
        def capitalize_match(m):
            return m.group(1) + m.group(2).upper()

        corrected = self.sentence_start_pattern.sub(capitalize_match, corrected)
        return corrected
