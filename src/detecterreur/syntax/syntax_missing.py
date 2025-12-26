import spacy

class SyntaxMissing:
    error_name = "SMIS"
    error_category = "SYNTAXE"

    def __init__(self, model="fr_core_news_sm"):
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

    def get_error(self, sentence: str):
        """
        Returns: (error_category, error_name, True/False)
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
        Attempts to fix the sentence by inserting missing elements.
        - Nouns: Inserts 'le', 'la', 'l'', or 'les'.
        - Verbs: Inserts 'Il' (dummy subject).
        Returns the reconstructed string.
        """
        doc = self.nlp(sentence)

        # List of tuples: (index, text_to_insert_before)
        insertions = []

        for token in doc:
            # Fix Missing Subject -> Insert "Il "
            if token.pos_ == "VERB":
                if (not self._is_imperative(token) and
                    not self._is_infinitive_or_participle(token) and
                    not self._has_subject(token)):
                    insertions.append((token.i, "Il "))

            # Fix Missing Determiner -> Insert "le ", "la ", "l'", "les "
            if token.pos_ == "NOUN":
                if (not self._is_proper_noun_or_pronoun(token) and
                    not self._is_predicate_noun(token) and
                    not self._is_mass_noun_or_plural(token) and
                    not self._has_determiner(token)):
                    det = self._guess_determiner(token)
                    insertions.append((token.i, det))

        # Reconstruct the sentence with insertions
        result_tokens = []
        insertion_map = dict(insertions)  # {index: "text to insert"}

        for i, token in enumerate(doc):
            if i in insertion_map:
                # Insert the missing word before the current token
                to_insert = insertion_map[i]
                if to_insert.endswith("'"):
                    result_tokens.append(to_insert + token.text)
                else:
                    result_tokens.append(to_insert.strip() + " " + token.text)
            else:
                result_tokens.append(token.text)

            # Add whitespace if the original token had it
            if token.whitespace_:
                result_tokens[-1] += token.whitespace_

        # Join the tokens to form the final string
        final_str = "".join(result_tokens)
        return final_str.strip()

    # ----------------------------------------------------------------------
    # Heuristics
    # ----------------------------------------------------------------------
    def _guess_determiner(self, token):
        """Guess the best article based on spaCy Morph analysis."""
        morph = token.morph.to_dict()
        number = morph.get("Number", ["Sing"])[0]
        gender = morph.get("Gender", ["Masc"])[0]

        # Plural
        if number == "Plur":
            return "les "

        # Vowel check for elision (l')
        if token.text[0].lower() in "aeiouyéèêëàâ":
            return "l'"

        # Singular
        if gender == "Fem":
            return "la "

        return "le "

    # ----------------------------------------------------------------------
    # Detection Helpers
    # ----------------------------------------------------------------------
    def _is_sentence_fragment(self, doc):
        finite_verbs = [token for token in doc
                       if token.pos_ == "VERB"
                       and not self._is_infinitive_or_participle(token)]
        return len(finite_verbs) == 0

    def _is_imperative(self, verb_token):
        if verb_token.i == 0 or (verb_token.i > 0 and verb_token.doc[verb_token.i - 1].is_punct):
            if not self._has_subject(verb_token):
                return True
        return False

    def _is_infinitive_or_participle(self, verb_token):
        return "VerbForm=Inf" in verb_token.morph or "VerbForm=Part" in verb_token.morph

    def _has_subject(self, verb_token):
        subjects = [child for child in verb_token.children if child.dep_ in ["nsubj", "nsubj:pass"]]
        return len(subjects) > 0

    def _has_determiner(self, noun_token):
        dets = [child for child in noun_token.children if child.dep_ in ["det", "poss"]]
        return len(dets) > 0

    def _is_proper_noun_or_pronoun(self, noun_token):
        return noun_token.pos_ in ["PROPN", "PRON"]

    def _is_predicate_noun(self, noun_token):
        return noun_token.dep_ == "attr"

    def _is_mass_noun_or_plural(self, noun_token):
        if noun_token.head.pos_ == "ADP":
            return True
        return False

    def _preposition_has_object(self, prep_token):
        objects = [child for child in prep_token.children if child.dep_ == "pobj"]
        return len(objects) > 0
