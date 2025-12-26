import spacy

class SyntaxInsertion:
    error_name = "SINS"
    error_category = "SYNTAXE"
    
    def __init__(self, model="fr_core_news_sm"):
        if not spacy.util.is_package(model):
            spacy.cli.download(model)
        self.nlp = spacy.load(model)
        
        # Words that are structurally determiners but can legally coexist
        # e.g. "Tous les jours" -> "Tous" and "les" are both often tagged as dets
        self.allowed_predeterminers = {"tout", "tous", "toute", "toutes"}
        
        # Quantifiers that can precede determiners in French
        self.allowed_quantifiers = {"plusieurs", "quelques", "certains", "certaines", 
                                    "divers", "diverses", "chaque", "aucun", "aucune"}
        
        # Coordinating conjunctions that allow multiple subjects
        self.coordinating_conj = {"et", "ou", "ni"}
    
    def _has_coordination(self, subjects):
        """Check if subjects are coordinated with 'et', 'ou', 'ni'"""
        if len(subjects) < 2:
            return False
        
        # Check if there's a conjunction between subjects
        for i in range(len(subjects) - 1):
            subj1 = subjects[i]
            subj2 = subjects[i + 1]
            
            # Look for conj between the two subjects
            for token_idx in range(subj1.i + 1, subj2.i):
                token = subj1.doc[token_idx]
                if token.dep_ == "cc" and token.text.lower() in self.coordinating_conj:
                    return True
        return False
    
    def get_error(self, sentence: str):
        """
        Returns: (error_category, error_name, True/False)
        """
        doc = self.nlp(sentence)
        
        for token in doc:
            # Check 1: Nouns with multiple determiners
            if token.pos_ in ["NOUN", "PROPN"]:
                dets = [child for child in token.children if child.dep_ == "det"]
                
                # Filter out valid predeterminers and quantifiers
                conflicting_dets = [d for d in dets 
                                   if d.lemma_ not in self.allowed_predeterminers
                                   and d.lemma_ not in self.allowed_quantifiers]
                
                if len(conflicting_dets) > 1:
                    return self.error_category, self.error_name, True
            
            # Check 2: Verbs with multiple subjects (unconnected)
            if token.pos_ == "VERB":
                subjects = [child for child in token.children if child.dep_ == "nsubj"]
                
                # Only flag error if subjects are NOT coordinated
                if len(subjects) > 1 and not self._has_coordination(subjects):
                    return self.error_category, self.error_name, True
        
        return self.error_category, self.error_name, False
    
    def correct(self, sentence: str) -> str:
        """
        Removes the FIRST element of a conflicting pair.
        "Le mon frère" -> "mon frère"
        "Je tu manges" -> "tu manges"
        """
        doc = self.nlp(sentence)
        tokens_to_remove = set()
        
        for token in doc:
            # 1. Fix Double Determiners
            if token.pos_ in ["NOUN", "PROPN"]:
                dets = [child for child in token.children if child.dep_ == "det"]
                conflicting_dets = [d for d in dets 
                                   if d.lemma_ not in self.allowed_predeterminers
                                   and d.lemma_ not in self.allowed_quantifiers]
                
                if len(conflicting_dets) > 1:
                    # Sort by position to remove the first one structurally
                    conflicting_dets.sort(key=lambda t: t.i)
                    # Mark the first one for removal
                    tokens_to_remove.add(conflicting_dets[0].i)
            
            # 2. Fix Double Subjects (only if not coordinated)
            if token.pos_ == "VERB":
                subjects = [child for child in token.children if child.dep_ == "nsubj"]
                
                if len(subjects) > 1 and not self._has_coordination(subjects):
                    subjects.sort(key=lambda t: t.i)
                    tokens_to_remove.add(subjects[0].i)
        
        # Reconstruct sentence skipping marked tokens
        tokens = [t.text_with_ws for t in doc if t.i not in tokens_to_remove]
        return "".join(tokens).strip()