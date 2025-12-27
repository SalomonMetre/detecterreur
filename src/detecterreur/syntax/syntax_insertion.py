import spacy
from typing import Tuple, Set

class SyntaxInsertion:
    """
    Detects and corrects syntax insertion errors in French, such as:
    - Nouns with multiple conflicting determiners (e.g., "Le mon frère" → "mon frère").
    - Verbs with multiple uncoordinated subjects (e.g., "Je tu manges" → "tu manges").

    Category: SYNTAXE
    Error: SINS
    """
    error_name = "SINS"
    error_category = "SYNTAXE"

    def __init__(self, model: str = "fr_core_news_sm"):
        """
        Args:
            model (str): spaCy model to use for parsing.
        """
        if not spacy.util.is_package(model):
            spacy.cli.download(model)
        self.nlp = spacy.load(model)

        # Words that are structurally determiners but can legally coexist
        self.allowed_predeterminers = {"tout", "tous", "toute", "toutes"}

        # Quantifiers that can precede determiners in French
        self.allowed_quantifiers = {
            "plusieurs", "quelques", "certains", "certaines",
            "divers", "diverses", "chaque", "aucun", "aucune"
        }

        # Coordinating conjunctions that allow multiple subjects
        self.coordinating_conj = {"et", "ou", "ni"}

    def _has_coordination(self, subjects: list) -> bool:
        """
        Check if subjects are coordinated with 'et', 'ou', or 'ni'.
        Args:
            subjects (list): List of subject tokens.
        Returns:
            bool: True if subjects are coordinated.
        """
        if len(subjects) < 2:
            return False

        for i in range(len(subjects) - 1):
            subj1, subj2 = subjects[i], subjects[i + 1]
            for token_idx in range(subj1.i + 1, subj2.i):
                token = subj1.doc[token_idx]
                if token.dep_ == "cc" and token.text.lower() in self.coordinating_conj:
                    return True
        return False

    def get_error(self, sentence: str) -> Tuple[str, str, bool]:
        """
        Detects syntax insertion errors in the sentence.
        Returns:
            Tuple[str, str, bool]: (error_category, error_name, has_error)
        """
        doc = self.nlp(sentence)

        for token in doc:
            # Check 1: Nouns with multiple determiners
            if token.pos_ in ["NOUN", "PROPN"]:
                dets = [child for child in token.children if child.dep_ == "det"]
                conflicting_dets = [
                    d for d in dets
                    if d.lemma_ not in self.allowed_predeterminers
                    and d.lemma_ not in self.allowed_quantifiers
                ]
                if len(conflicting_dets) > 1:
                    return self.error_category, self.error_name, True

            # Check 2: Verbs with multiple subjects (unconnected)
            if token.pos_ == "VERB":
                subjects = [child for child in token.children if child.dep_ == "nsubj"]
                if len(subjects) > 1 and not self._has_coordination(subjects):
                    return self.error_category, self.error_name, True

        return self.error_category, self.error_name, False

    def correct(self, sentence: str) -> str:
        """
        Corrects syntax insertion errors by removing the first conflicting element.
        Returns:
            str: The corrected sentence.
        """
        doc = self.nlp(sentence)
        tokens_to_remove: Set[int] = set()

        for token in doc:
            # Fix 1: Double Determiners
            if token.pos_ in ["NOUN", "PROPN"]:
                dets = [child for child in token.children if child.dep_ == "det"]
                conflicting_dets = [
                    d for d in dets
                    if d.lemma_ not in self.allowed_predeterminers
                    and d.lemma_ not in self.allowed_quantifiers
                ]
                if len(conflicting_dets) > 1:
                    conflicting_dets.sort(key=lambda t: t.i)
                    tokens_to_remove.add(conflicting_dets[0].i)

            # Fix 2: Double Subjects (uncoordinated)
            if token.pos_ == "VERB":
                subjects = [child for child in token.children if child.dep_ == "nsubj"]
                if len(subjects) > 1 and not self._has_coordination(subjects):
                    subjects.sort(key=lambda t: t.i)
                    tokens_to_remove.add(subjects[0].i)

        # Reconstruct the sentence, skipping marked tokens
        corrected_tokens = [t.text_with_ws for i, t in enumerate(doc) if i not in tokens_to_remove]
        return "".join(corrected_tokens).strip()
