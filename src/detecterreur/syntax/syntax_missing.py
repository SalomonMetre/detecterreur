import spacy
from typing import Tuple, List, Dict

class SyntaxMissing:
    """
    Detects and corrects missing syntax elements in French sentences, such as:
    - Missing subjects for verbs.
    - Missing determiners for nouns.
    - Missing objects for prepositions.

    Category: SYNTAXE
    Error: SMIS
    """
    error_name = "SMIS"
    error_category = "SYNTAXE"

    def __init__(self, model: str = "fr_core_news_sm"):
        """
        Args:
            model (str): spaCy model to use for parsing.
        """
        if not spacy.util.is_package(model):
            spacy.cli.download(model)
        self.nlp = spacy.load(model)

        # Indicators for imperative mood
        self.imperative_indicators = {"!", "."}

        # Prepositions that MUST have an object
        self.prepositions_need_object = {
            "à", "de", "dans", "pour", "avec", "sans", "sur", "sous",
            "par", "entre", "vers", "chez", "durant", "pendant"
        }

        # Auxiliaries
        self.auxiliaries = {"avoir", "être"}

    def get_error(self, sentence: str) -> Tuple[str, str, bool]:
        """
        Detects missing syntax elements in the sentence.
        Returns:
            Tuple[str, str, bool]: (error_category, error_name, has_error)
        """
        doc = self.nlp(sentence)

        # Check 1: Sentence fragments (no finite verb)
        if len(doc) > 2 and self._is_sentence_fragment(doc):
            return self.error_category, self.error_name, True

        for token in doc:
            # Check 2: Verbs without subjects
            if token.pos_ == "VERB":
                if (not self._is_imperative(token) and
                    not self._is_infinitive_or_participle(token)):
                    if not self._has_subject(token):
                        return self.error_category, self.error_name, True

            # Check 3: Nouns without determiners
            if token.pos_ == "NOUN":
                if (not self._is_proper_noun_or_pronoun(token) and
                    not self._is_predicate_noun(token) and
                    not self._is_mass_noun_or_plural(token)):
                    if not self._has_determiner(token):
                        return self.error_category, self.error_name, True

            # Check 4: Prepositions without objects
            if token.pos_ == "ADP" and token.lemma_ in self.prepositions_need_object:
                if not self._preposition_has_object(token):
                    if token.i == len(doc) - 1 or doc[token.i + 1].is_punct:
                        return self.error_category, self.error_name, True

        return self.error_category, self.error_name, False

    def correct(self, sentence: str) -> str:
        """
        Corrects missing syntax elements in the sentence.
        Returns:
            str: The corrected sentence.
        """
        doc = self.nlp(sentence)
        insertions: List[Tuple[int, str]] = []

        for token in doc:
            # Fix: Missing Subject → Insert "Il "
            if token.pos_ == "VERB":
                if (not self._is_imperative(token) and
                    not self._is_infinitive_or_participle(token) and
                    not self._has_subject(token)):
                    insertions.append((token.i, "Il "))

            # Fix: Missing Determiner → Insert "le ", "la ", "l'", or "les "
            if token.pos_ == "NOUN":
                if (not self._is_proper_noun_or_pronoun(token) and
                    not self._is_predicate_noun(token) and
                    not self._is_mass_noun_or_plural(token) and
                    not self._has_determiner(token)):
                    det = self._guess_determiner(token)
                    insertions.append((token.i, det))

        # Reconstruct the sentence with insertions
        result_tokens = []
        insertion_map: Dict[int, str] = dict(insertions)

        for i, token in enumerate(doc):
            if i in insertion_map:
                to_insert = insertion_map[i]
                if to_insert.endswith("'"):
                    result_tokens.append(to_insert + token.text)
                else:
                    result_tokens.append(to_insert.strip() + " " + token.text)
            else:
                result_tokens.append(token.text)

            if token.whitespace_:
                result_tokens[-1] += token.whitespace_

        return "".join(result_tokens).strip()

    # ----------------------------------------------------------------------
    # Heuristics
    # ----------------------------------------------------------------------
    def _guess_determiner(self, token: spacy.tokens.Token) -> str:
        """
        Guesses the best article based on spaCy Morph analysis.
        Returns:
            str: The guessed determiner.
        """
        morph = token.morph.to_dict()
        number = morph.get("Number", ["Sing"])[0]
        gender = morph.get("Gender", ["Masc"])[0]

        if number == "Plur":
            return "les "
        if token.text[0].lower() in "aeiouyéèêëàâ":
            return "l'"
        if gender == "Fem":
            return "la "
        return "le "

    # ----------------------------------------------------------------------
    # Detection Helpers
    # ----------------------------------------------------------------------
    def _is_sentence_fragment(self, doc: spacy.tokens.Doc) -> bool:
        """
        Checks if the sentence is a fragment (no finite verb).
        Returns:
            bool: True if the sentence is a fragment.
        """
        finite_verbs = [
            token for token in doc
            if token.pos_ == "VERB" and not self._is_infinitive_or_participle(token)
        ]
        return len(finite_verbs) == 0

    def _is_imperative(self, verb_token: spacy.tokens.Token) -> bool:
        """
        Checks if the verb is in imperative mood.
        Returns:
            bool: True if the verb is imperative.
        """
        if verb_token.i == 0 or (verb_token.i > 0 and verb_token.doc[verb_token.i - 1].is_punct):
            if not self._has_subject(verb_token):
                return True
        return False

    def _is_infinitive_or_participle(self, verb_token: spacy.tokens.Token) -> bool:
        """
        Checks if the verb is in infinitive or participle form.
        Returns:
            bool: True if the verb is infinitive or participle.
        """
        return "VerbForm=Inf" in verb_token.morph or "VerbForm=Part" in verb_token.morph

    def _has_subject(self, verb_token: spacy.tokens.Token) -> bool:
        """
        Checks if the verb has a subject.
        Returns:
            bool: True if the verb has a subject.
        """
        subjects = [child for child in verb_token.children if child.dep_ in ["nsubj", "nsubj:pass"]]
        return len(subjects) > 0

    def _has_determiner(self, noun_token: spacy.tokens.Token) -> bool:
        """
        Checks if the noun has a determiner.
        Returns:
            bool: True if the noun has a determiner.
        """
        dets = [child for child in noun_token.children if child.dep_ in ["det", "poss"]]
        return len(dets) > 0

    def _is_proper_noun_or_pronoun(self, noun_token: spacy.tokens.Token) -> bool:
        """
        Checks if the token is a proper noun or pronoun.
        Returns:
            bool: True if the token is a proper noun or pronoun.
        """
        return noun_token.pos_ in ["PROPN", "PRON"]

    def _is_predicate_noun(self, noun_token: spacy.tokens.Token) -> bool:
        """
        Checks if the noun is a predicate noun.
        Returns:
            bool: True if the noun is a predicate noun.
        """
        return noun_token.dep_ == "attr"

    def _is_mass_noun_or_plural(self, noun_token: spacy.tokens.Token) -> bool:
        """
        Checks if the noun is a mass noun or plural.
        Returns:
            bool: True if the noun is a mass noun or plural.
        """
        if noun_token.head.pos_ == "ADP":
            return True
        return False

    def _preposition_has_object(self, prep_token: spacy.tokens.Token) -> bool:
        """
        Checks if the preposition has an object.
        Returns:
            bool: True if the preposition has an object.
        """
        objects = [child for child in prep_token.children if child.dep_ == "pobj"]
        return len(objects) > 0
