import re
from typing import Tuple, List, Optional
from pygrammalecte import grammalecte_text, GrammalecteGrammarMessage

class FormCase:
    """
    Detects and corrects capitalization errors in French:
    - Sentence starts (after punctuation or at the beginning of the text).
    - Proper nouns (using Grammalecte, with strict filtering).

    SAFETY V2:
    - Uses strict regex for sentence starts.
    - Uses Grammalecte for proper nouns but filters out hallucinations.
    - Rejects any suggestion that changes the word's spelling (e.g., "c'est" -> "A'est").

    Category: FORME
    Error: FMAJ
    """
    error_name = "FMAJ"
    error_category = "FORME"

    def __init__(self):
        # Regex for sentence starts:
        # Group 1: Start of line OR (.!? + whitespace)
        # Group 2: The lowercase letter to fix
        self.sentence_start_pattern = re.compile(r'(^|[.!?]\s+)([a-zàâéèêëîïôùûüç])')

    # -------------------------------
    # Public API
    # -------------------------------
    def get_error(self, sentence: str) -> Tuple[str, str, bool]:
        """
        Detects capitalization errors in the sentence.
        Returns:
            Tuple[str, str, bool]: (error_category, error_name, has_error)
        """
        # 1. Regex Check (Fast & Deterministic)
        if self.sentence_start_pattern.search(sentence):
            return self.error_category, self.error_name, True

        # 2. Grammalecte Check (For proper nouns mid-sentence)
        for message in grammalecte_text(sentence):
            if isinstance(message, GrammalecteGrammarMessage):
                if self._is_capitalization_error(message):
                    original = sentence[message.start:message.end]
                    if message.suggestions:
                        sugg = message.suggestions[0]
                        if original.lower() == sugg.lower():
                            return self.error_category, self.error_name, True

        return self.error_category, self.error_name, False

    def correct(self, sentence: str) -> str:
        """
        Corrects capitalization errors in the sentence.
        Returns:
            str: The corrected sentence.
        """
        corrected = sentence

        # 1. Regex First (Sentence Starts) - The most reliable fix
        def capitalize_match(m):
            return m.group(1) + m.group(2).upper()

        corrected = self.sentence_start_pattern.sub(capitalize_match, corrected)

        # 2. Grammalecte Second (Proper Nouns) - With Strict Filtering
        suggestions_to_apply = []

        # Run detection on the ALREADY regex-corrected string to avoid conflicts
        for message in grammalecte_text(corrected):
            if isinstance(message, GrammalecteGrammarMessage):
                if self._is_capitalization_error(message) and message.suggestions:
                    original = corrected[message.start:message.end]
                    suggestion = message.suggestions[0]

                    # STRICT FILTER: Only accept if it's the SAME word, just capitalized
                    if original.lower() == suggestion.lower():
                        suggestions_to_apply.append((message.start, message.end, suggestion))

        # Apply Right-to-Left to avoid offset issues
        suggestions_to_apply.sort(key=lambda x: x[0], reverse=True)

        for start, end, replacement in suggestions_to_apply:
            corrected = corrected[:start] + replacement + corrected[end:]

        return corrected

    # -------------------------------
    # Internal Logic
    # -------------------------------
    def _is_capitalization_error(self, message: GrammalecteGrammarMessage) -> bool:
        """
        Checks if Grammalecte flagged a capitalization issue.
        Args:
            message: GrammalecteGrammarMessage object.
        Returns:
            bool: True if the message is about capitalization.
        """
        if hasattr(message, "type") and message.type == "maj":
            return True
        if "majuscule" in message.message.lower():
            return True
        return False
