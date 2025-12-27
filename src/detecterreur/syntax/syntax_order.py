import spacy
from typing import Tuple, List, Set, Optional

class SyntaxOrder:
    """
    Detects and corrects syntax order errors in French sentences, such as:
    - Adjective-noun order (BAGS adjectives must come before the noun).
    - Subject-verb order (subject before verb in declarative sentences).
    - Pronoun-verb order (object pronouns must come before the verb).
    - Negation order (ne ... pas).
    - Determiner-noun order (determiner before noun).

    Category: SYNTAXE
    Error: SORD
    """
    error_name = "SORD"
    error_category = "SYNTAXE"

    def __init__(self, model: str = "fr_core_news_sm"):
        """
        Args:
            model (str): spaCy model to use for parsing.
        """
        if not spacy.util.is_package(model):
            spacy.cli.download(model)
        self.nlp = spacy.load(model)

        # BAGS Adjectives (must come before noun)
        self.pre_noun_adjectives: Set[str] = {
            "beau", "joli", "laid", "jeune", "vieux", "nouveau",
            "ancien", "bon", "mauvais", "meilleur", "pire",
            "grand", "gros", "petit", "long", "court", "haut",
            "bas", "énorme", "immense", "minuscule", "large", "étroit",
            "autre", "premier", "deuxième", "dernier"
        }

        # Object pronouns (must come before verb)
        self.object_pronouns: Set[str] = {
            "me", "te", "le", "la", "les", "lui", "leur", "y", "en",
            "se", "m'", "t'", "l'", "s'"
        }

        # Negation parts
        self.negation_first: Set[str] = {"ne", "n'"}
        self.negation_second: Set[str] = {
            "pas", "plus", "jamais", "rien", "personne", "guère", "point"
        }

    def get_error(self, sentence: str) -> Tuple[str, str, bool]:
        """
        Detects syntax order errors in the sentence.
        Returns:
            Tuple[str, str, bool]: (error_category, error_name, has_error)
        """
        doc = self.nlp(sentence)

        checks = [
            self._check_determiner_noun_order(doc),
            self._check_adjective_noun_order(doc),
            self._check_subject_verb_order(doc),
            self._check_pronoun_verb_order(doc),
            self._check_negation_order(doc),
        ]

        for has_error, _ in checks:
            if has_error:
                return self.error_category, self.error_name, True

        return self.error_category, self.error_name, False

    def correct(self, sentence: str) -> str:
        """
        Corrects syntax order errors in the sentence.
        Returns:
            str: The corrected sentence or a suggestion.
        """
        doc = self.nlp(sentence)

        if self._check_determiner_noun_order(doc)[0]:
            return self._fix_determiner_noun_order(doc)

        if self._check_adjective_noun_order(doc)[0]:
            return self._fix_adjective_noun_order(doc)

        if self._check_subject_verb_order(doc)[0]:
            return self._fix_subject_verb_order(doc)

        if self._check_pronoun_verb_order(doc)[0]:
            return self._fix_pronoun_verb_order(doc)

        if self._check_negation_order(doc)[0]:
            return "SUGGESTION: Reorder negation (ne + verb + pas)"

        return sentence

    # ----------------------------------------------------------------------
    # Detection Logic
    # ----------------------------------------------------------------------

    def _check_adjective_noun_order(self, doc: spacy.tokens.Doc) -> Tuple[bool, Optional[str]]:
        """
        Checks if BAGS adjectives are misplaced after the noun.
        Returns:
            Tuple[bool, Optional[str]]: (has_error, error_message)
        """
        for token in doc:
            if token.pos_ == "NOUN":
                for child in token.children:
                    if (child.pos_ == "ADJ" and
                        child.lemma_.lower() in self.pre_noun_adjectives and
                        child.i > token.i):
                        return True, f"Adjective '{child.text}' should occur before '{token.text}'"
        return False, None

    def _check_subject_verb_order(self, doc: spacy.tokens.Doc) -> Tuple[bool, Optional[str]]:
        """
        Checks if the subject is misplaced after the verb in declarative sentences.
        Returns:
            Tuple[bool, Optional[str]]: (has_error, error_message)
        """
        for token in doc:
            if token.pos_ == "VERB":
                subjects = [c for c in token.children if c.dep_ in ["nsubj", "nsubj:pass"]]
                for subject in subjects:
                    if subject.i > token.i:
                        if self._is_question(doc) or self._is_imperative_form(token):
                            continue
                        return True, "Subject misplaced (VS order)"
        return False, None

    def _check_pronoun_verb_order(self, doc: spacy.tokens.Doc) -> Tuple[bool, Optional[str]]:
        """
        Checks if object pronouns are misplaced after the verb.
        Returns:
            Tuple[bool, Optional[str]]: (has_error, error_message)
        """
        for token in doc:
            if token.pos_ == "VERB" and not self._is_imperative_form(token):
                for child in token.children:
                    if (child.pos_ == "PRON" and
                        child.lemma_.lower() in self.object_pronouns and
                        child.dep_ in ["obj", "iobj", "expl:pv"] and
                        child.i > token.i):
                        return True, "Object pronoun misplaced"

                # Check for "orphan" determiners treated as pronouns
                next_tokens = doc[token.i+1 : token.i+3]
                for t in next_tokens:
                    if (t.text.lower() in ["le", "la", "les"] and
                        t.pos_ == "DET" and
                        t.head == token):
                        return True, "Determiner used as pronoun misplaced"
        return False, None

    def _check_negation_order(self, doc: spacy.tokens.Doc) -> Tuple[bool, Optional[str]]:
        """
        Checks if negation parts are misplaced.
        Returns:
            Tuple[bool, Optional[str]]: (has_error, error_message)
        """
        for token in doc:
            if token.pos_ in ["VERB", "AUX"]:
                ne_part = None
                pas_part = None
                for child in token.children:
                    if child.lemma_.lower() in self.negation_first:
                        ne_part = child
                    if child.lemma_.lower() in self.negation_second:
                        pas_part = child

                if pas_part and pas_part.i < token.i:
                    return True, "Negation 'pas' should be after verb"
        return False, None

    def _check_determiner_noun_order(self, doc: spacy.tokens.Doc) -> Tuple[bool, Optional[str]]:
        """
        Checks if determiners are misplaced after the noun.
        Returns:
            Tuple[bool, Optional[str]]: (has_error, error_message)
        """
        for token in doc:
            if token.pos_ == "NOUN":
                dets = [c for c in token.children if c.dep_ == "det"]
                for det in dets:
                    if det.i > token.i:
                        return True, "Determiner misplaced"
        return False, None

    # ----------------------------------------------------------------------
    # Correction Helpers
    # ----------------------------------------------------------------------

    def _fix_adjective_noun_order(self, doc: spacy.tokens.Doc) -> str:
        """
        Fixes misplaced BAGS adjectives.
        Returns:
            str: The corrected sentence.
        """
        tokens: List[str] = []
        skip_indices: Set[int] = set()
        for token in doc:
            if token.i in skip_indices:
                continue
            if token.pos_ == "NOUN":
                misplaced = [
                    c for c in token.children
                    if (c.pos_ == "ADJ" and
                        c.lemma_.lower() in self.pre_noun_adjectives and
                        c.i > token.i)
                ]
                if misplaced:
                    for adj in misplaced:
                        tokens.append(adj.text)
                        skip_indices.add(adj.i)
                    tokens.append(token.text)
                else:
                    tokens.append(token.text)
            else:
                tokens.append(token.text)
        return " ".join(tokens)

    def _fix_determiner_noun_order(self, doc: spacy.tokens.Doc) -> str:
        """
        Fixes misplaced determiners.
        Returns:
            str: The corrected sentence.
        """
        tokens: List[str] = []
        skip_indices: Set[int] = set()
        for token in doc:
            if token.i in skip_indices:
                continue
            if token.pos_ == "NOUN":
                misplaced = [c for c in token.children if c.dep_ == "det" and c.i > token.i]
                if misplaced:
                    for det in misplaced:
                        tokens.append(det.text)
                        skip_indices.add(det.i)
                    tokens.append(token.text)
                else:
                    tokens.append(token.text)
            else:
                tokens.append(token.text)
        return " ".join(tokens)

    def _fix_pronoun_verb_order(self, doc: spacy.tokens.Doc) -> str:
        """
        Fixes misplaced object pronouns.
        Returns:
            str: The corrected sentence or a suggestion.
        """
        for token in doc:
            if token.pos_ == "VERB":
                for j in range(token.i + 1, min(len(doc), token.i + 3)):
                    cand = doc[j]
                    if cand.text.lower() in ["le", "la", "les", "me", "te", "se"]:
                        return f"SUGGESTION: Move '{cand.text}' before '{token.text}' -> '... {cand.text} {token.text} ...'"
        return " ".join([t.text for t in doc])

    def _fix_subject_verb_order(self, doc: spacy.tokens.Doc) -> str:
        """
        Fixes misplaced subjects.
        Returns:
            str: The corrected sentence.
        """
        tokens: List[str] = []
        skip_indices: Set[int] = set()
        for token in doc:
            if token.i in skip_indices:
                continue
            if token.pos_ == "VERB":
                misplaced = [c for c in token.children if c.dep_ == "nsubj" and c.i > token.i]
                if misplaced:
                    for subj in misplaced:
                        tokens.append(subj.text)
                        skip_indices.add(subj.i)
                    tokens.append(token.text)
                else:
                    tokens.append(token.text)
            else:
                tokens.append(token.text)
        return " ".join(tokens)

    # ----------------------------------------------------------------------
    # Utilities
    # ----------------------------------------------------------------------

    def _is_question(self, doc: spacy.tokens.Doc) -> bool:
        """
        Checks if the sentence is a question.
        Returns:
            bool: True if the sentence is a question.
        """
        if doc[-1].text == "?":
            return True
        for i in range(len(doc) - 1):
            if (doc[i].pos_ == "VERB" and doc[i+1].pos_ == "PRON" and
                "-" in doc[i].text_with_ws):
                return True
        return False

    def _is_imperative_form(self, verb_token: spacy.tokens.Token) -> bool:
        """
        Checks if the verb is in imperative form.
        Returns:
            bool: True if the verb is in imperative form.
        """
        subjects = [c for c in verb_token.children if c.dep_ == "nsubj"]
        return len(subjects) == 0
