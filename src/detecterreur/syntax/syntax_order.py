import spacy

class SyntaxOrder:
    error_name = "SORD"
    error_category = "SYNTAXE"
    
    def __init__(self, model="fr_core_news_sm"):
        if not spacy.util.is_package(model):
            spacy.cli.download(model)
        self.nlp = spacy.load(model)
        
        # BAGS Adjectives (Must come BEFORE noun)
        # We use LEMMAS here (dictionary form)
        self.pre_noun_adjectives = {
            "beau", "joli", "laid", "jeune", "vieux", "nouveau", 
            "ancien", "bon", "mauvais", "meilleur", "pire", 
            "grand", "gros", "petit", "long", "court", "haut", 
            "bas", "énorme", "immense", "minuscule", "large", "étroit",
            "autre", "premier", "deuxième", "dernier"
        }
        
        # Object pronouns (Must come BEFORE verb)
        self.object_pronouns = {
            "me", "te", "le", "la", "les", "lui", "leur", "y", "en",
            "se", "m'", "t'", "l'", "s'"
        }
        
        self.negation_first = {"ne", "n'"}
        self.negation_second = {"pas", "plus", "jamais", "rien", "personne", "guère", "point"}

    def get_error(self, sentence: str):
        doc = self.nlp(sentence)
        
        checks = [
            self._check_determiner_noun_order(doc),
            self._check_adjective_noun_order(doc),
            self._check_subject_verb_order(doc),
            self._check_pronoun_verb_order(doc),
            self._check_negation_order(doc),
        ]
        
        for has_error, msg in checks:
            if has_error:
                return self.error_category, self.error_name, True
        
        return self.error_category, self.error_name, False

    def correct(self, sentence: str) -> str:
        doc = self.nlp(sentence)
        
        # Apply corrections
        # Note: We return immediately after one type of fix to avoid
        # messing up indices. In a loop, we would re-parse.
        
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
    # Improved Detection Logic
    # ----------------------------------------------------------------------
    def _check_adjective_noun_order(self, doc):
        for token in doc:
            if token.pos_ == "NOUN":
                for child in token.children:
                    # Check if it's an ADJ and belongs to the BAGS list
                    if child.pos_ == "ADJ" and child.lemma_.lower() in self.pre_noun_adjectives:
                        # Error if it appears AFTER the noun
                        if child.i > token.i:
                            return True, f"Adjective '{child.text}' should occur before '{token.text}'"
        return False, None

    def _check_subject_verb_order(self, doc):
        for token in doc:
            if token.pos_ == "VERB":
                # Strict check for declarative sentences: Subject should be BEFORE verb
                subjects = [c for c in token.children if c.dep_ in ["nsubj", "nsubj:pass"]]
                
                for subject in subjects:
                    # If subject is AFTER verb
                    if subject.i > token.i:
                        # Exceptions: Questions, Inversion?
                        if self._is_question(doc) or self._is_imperative_form(token):
                            continue
                        
                        # "Mange je" -> Error
                        return True, "Subject misplaced (VS order)"
        return False, None

    def _check_pronoun_verb_order(self, doc):
        for token in doc:
            if token.pos_ == "VERB" and not self._is_imperative_form(token):
                
                # 1. Standard Object Pronouns (me, te, se...)
                for child in token.children:
                    if (child.pos_ == "PRON" and 
                        child.lemma_.lower() in self.object_pronouns and
                        child.dep_ in ["obj", "iobj", "expl:pv"]):
                        
                        if child.i > token.i:
                            return True, "Object pronoun misplaced"

                # 2. "Orphan" Determiners treated as Pronouns
                # Example: "Je vois le." -> spaCy tags 'le' as DET, dependent on 'vois' (or root)
                # We catch DETs that are physically AFTER the verb and have NO noun children
                next_tokens = doc[token.i+1 : token.i+3] # Look at 2 tokens after verb
                for t in next_tokens:
                    if t.text.lower() in ["le", "la", "les"] and t.pos_ == "DET":
                        # Check if this DET actually attaches to a Noun later?
                        # If its head is the verb, it's likely a mis-tagged pronoun error
                        if t.head == token:
                            return True, "Determiner used as pronoun misplaced"

        return False, None

    def _check_negation_order(self, doc):
        for token in doc:
            # Find the verb
            if token.pos_ in ["VERB", "AUX"]:
                
                # Check children for negation parts
                ne_part = None
                pas_part = None
                
                for child in token.children:
                    if child.lemma_.lower() in self.negation_first:
                        ne_part = child
                    if child.lemma_.lower() in self.negation_second:
                        pas_part = child
                
                # Case 1: "Je pas mange" -> pas is before verb
                if pas_part and pas_part.i < token.i:
                     return True, "Negation 'pas' should be after verb"
                     
                # Case 2: "Je ne mange pas" is correct. "Je ne pas mange" (ne & pas both before)
                # If 'pas' is before, it's an error.
                
        return False, None

    def _check_determiner_noun_order(self, doc):
        for token in doc:
            if token.pos_ == "NOUN":
                dets = [c for c in token.children if c.dep_ == "det"]
                for det in dets:
                    if det.i > token.i:
                        return True, "Determiner misplaced"
        return False, None

    # ----------------------------------------------------------------------
    # Correction Helpers (Re-builders)
    # ----------------------------------------------------------------------
    def _fix_adjective_noun_order(self, doc):
        tokens = []
        skip_indices = set()
        for token in doc:
            if token.i in skip_indices: continue
            if token.pos_ == "NOUN":
                misplaced = [c for c in token.children 
                             if c.pos_ == "ADJ" 
                             and c.lemma_.lower() in self.pre_noun_adjectives 
                             and c.i > token.i]
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

    def _fix_determiner_noun_order(self, doc):
        tokens = []
        skip_indices = set()
        for token in doc:
            if token.i in skip_indices: continue
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
    
    def _fix_pronoun_verb_order(self, doc):
        # Basic heuristic: find the misplaced 'le' after verb and move it before
        tokens = [t.text for t in doc]
        
        for token in doc:
            if token.pos_ == "VERB":
                # Look for that "Orphan DET" or misplaced PRON
                for j in range(token.i + 1, min(len(doc), token.i + 3)):
                    cand = doc[j]
                    if cand.text.lower() in ["le", "la", "les", "me", "te", "se"]:
                        # Swap!
                        # We reconstruct: ... [cand] [verb] ...
                        # This is tricky with indices, so we return a simple suggestion string
                        return f"SUGGESTION: Move '{cand.text}' before '{token.text}' -> '... {cand.text} {token.text} ...'"
        return " ".join(tokens)

    def _fix_subject_verb_order(self, doc):
        tokens = []
        skip_indices = set()
        for token in doc:
            if token.i in skip_indices: continue
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
    def _is_question(self, doc):
        if doc[-1].text == "?": return True
        # Check for inversion (Verb-Pronoun)
        for i in range(len(doc)-1):
            if doc[i].pos_ == "VERB" and doc[i+1].pos_ == "PRON":
                # Simply checking if hyphenated might be safer, but loose check:
                if "-" in doc[i].text_with_ws: return True
        return False
    
    def _is_imperative_form(self, verb_token):
        subjects = [c for c in verb_token.children if c.dep_ == "nsubj"]
        return len(subjects) == 0