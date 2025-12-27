import spacy
from typing import Tuple, List

class SyntaxRedundancy:
    """
    Detects and corrects redundant words in French sentences.
    Handles valid repetitions (e.g., reflexive pronouns, intensifiers) and removes invalid ones.

    Category: SYNTAXE
    Error: SRED
    """
    error_name = "SRED"
    error_category = "SYNTAXE"

    def __init__(self, model: str = "fr_core_news_sm"):
        """
        Args:
            model (str): spaCy model to use for parsing.
        """
        if not spacy.util.is_package(model):
            spacy.cli.download(model)
        self.nlp = spacy.load(model)

        # Reflexive pronouns that can validly double (e.g., "nous nous")
        self.reflexive_pronouns: set = {"me", "te", "se", "nous", "vous"}

        # Words that can be intensified by repetition (e.g., "très très")
        self.valid_intensifiers: set = {"très", "bien", "tout", "super"}

    def _is_valid_reflexive(self, token: spacy.tokens.Token, next_token: spacy.tokens.Token) -> bool:
        """
        Checks if the repetition is a valid reflexive construction (e.g., "nous nous").
        Args:
            token: Current token.
            next_token: Next token.
        Returns:
            bool: True if the repetition is valid.
        """
        return (
            token.text.lower() in self.reflexive_pronouns
            and token.text.lower() == next_token.text.lower()
            and token.pos_ == "PRON"
            and next_token.pos_ == "PRON"
        )

    def _is_valid_intensifier(self, token: spacy.tokens.Token, next_token: spacy.tokens.Token) -> bool:
        """
        Checks if the repetition is a valid intensifier (e.g., "très très").
        Args:
            token: Current token.
            next_token: Next token.
        Returns:
            bool: True if the repetition is valid.
        """
        return (
            token.text.lower() in self.valid_intensifiers
            and token.text.lower() == next_token.text.lower()
        )

    def get_error(self, sentence: str) -> Tuple[str, str, bool]:
        """
        Detects redundant words in the sentence.
        Returns:
            Tuple[str, str, bool]: (error_category, error_name, has_error)
        """
        doc = self.nlp(sentence)

        for i in range(len(doc) - 1):
            token = doc[i]
            next_token = doc[i + 1]

            # Check for identical text (case-insensitive)
            if token.text.lower() == next_token.text.lower():
                # Ignore punctuation
                if token.is_punct:
                    continue

                # Check for valid French repetitions
                if self._is_valid_reflexive(token, next_token):
                    continue

                if self._is_valid_intensifier(token, next_token):
                    continue

                # Found invalid repetition
                return self.error_category, self.error_name, True

        return self.error_category, self.error_name, False

    def correct(self, sentence: str) -> str:
        """
        Removes redundant words while preserving spacing.
        Returns:
            str: The corrected sentence.
        """
        doc = self.nlp(sentence)
        tokens_to_keep: List[str] = []
        i = 0

        while i < len(doc):
            token = doc[i]

            # Look ahead
            if i < len(doc) - 1:
                next_token = doc[i + 1]

                # Check if this is an invalid repetition
                if (
                    token.text.lower() == next_token.text.lower()
                    and not token.is_punct
                    and not self._is_valid_reflexive(token, next_token)
                    and not self._is_valid_intensifier(token, next_token)
                ):
                    # Keep the first token and skip the second
                    tokens_to_keep.append(token.text_with_ws)
                    i += 2
                    continue

            tokens_to_keep.append(token.text_with_ws)
            i += 1

        return "".join(tokens_to_keep).strip()
