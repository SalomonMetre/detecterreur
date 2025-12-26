import re
from typing import Tuple, List
from pygrammalecte import grammalecte_text, GrammalecteGrammarMessage

class FormCase:
    """
    Detects capitalization errors (sentence starts, proper nouns missing caps).
    Category: FORME
    Error: FMAJ
    """
    error_name = "FMAJ"
    error_category = "FORME"

    def __init__(self):
        # Regex to find lowercase words following sentence boundaries:
        # Group 1: Start of string OR (.!? + whitespace)
        # Group 2: The alphanumeric character that should be uppercase
        self.sentence_start_pattern = re.compile(r'(^|[.!?]\s+)([a-zàâéèêëîïôùûüç])')

    # -------------------------------
    # Public API
    # -------------------------------

    def get_error(self, sentence: str) -> Tuple[str, str, bool]:
        """
        Returns: (error_category, error_name, True/False)
        """
        # 1. Fast Regex Check (Sentence starts)
        # We iterate to find at least one match
        if self.sentence_start_pattern.search(sentence):
             return self.error_category, self.error_name, True

        # 2. Deep Check (Grammalecte)
        # Useful for proper nouns (e.g., "paris" -> "Paris") which regex won't catch mid-sentence
        for message in grammalecte_text(sentence):
            if isinstance(message, GrammalecteGrammarMessage):
                # Check if the error is related to capitalization
                # Note: message attributes vary by version, checking text is robust
                if "majuscule" in message.message.lower() or (hasattr(message, "type") and message.type == "maj"):
                    return self.error_category, self.error_name, True

        return self.error_category, self.error_name, False

    def correct(self, sentence: str) -> str:
        """
        Corrects capitalization using Grammalecte (smart) + Regex (structural fallback).
        """
        corrected = sentence

        # 1. Apply Grammalecte suggestions
        # We must collect ALL suggestions first, then apply them from Right-to-Left
        # to avoid messing up the indices of subsequent errors.
        
        suggestions_to_apply = []
        for message in grammalecte_text(corrected):
            if isinstance(message, GrammalecteGrammarMessage):
                if "majuscule" in message.message.lower() or (hasattr(message, "type") and message.type == "maj"):
                    if message.suggestions:
                        # Store (start, end, replacement)
                        suggestions_to_apply.append((int(message.start), int(message.end), message.suggestions[0]))

        # Sort by start index DESCENDING (Right-to-Left)
        suggestions_to_apply.sort(key=lambda x: x[0], reverse=True)

        for start, end, replacement in suggestions_to_apply:
            corrected = corrected[:start] + replacement + corrected[end:]

        # 2. Apply Regex Fallback
        # This handles simple sentence starts that Grammalecte might miss or label differently
        def capitalize_match(m):
            # m.group(1) is the prefix (e.g., ". " or "")
            # m.group(2) is the letter to capitalize
            return m.group(1) + m.group(2).upper()

        corrected = self.sentence_start_pattern.sub(capitalize_match, corrected)
        
        return corrected