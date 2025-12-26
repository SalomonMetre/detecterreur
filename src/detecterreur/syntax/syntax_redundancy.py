import spacy

class SyntaxRedundancy:
    
    error_name = "SRED"
    error_category = "SYNTAXE"
    
    def __init__(self, model="fr_core_news_sm"):
        if not spacy.util.is_package(model):
            spacy.cli.download(model)
        self.nlp = spacy.load(model)
        
        # Reflexive pronouns that can validly double
        self.reflexive_pronouns = {"me", "te", "se", "nous", "vous"}
        
        # Words that can be intensified by repetition
        self.valid_intensifiers = {"très", "bien", "tout", "super"}
        
    def _is_valid_reflexive(self, token, next_token):
        """Check if this is a valid reflexive construction like 'nous nous'"""
        return (token.text.lower() in self.reflexive_pronouns 
                and token.text.lower() == next_token.text.lower()
                and token.pos_ == "PRON" 
                and next_token.pos_ == "PRON")
    
    def _is_valid_intensifier(self, token, next_token):
        """Check if this is valid intensification like 'très très'"""
        return (token.text.lower() in self.valid_intensifiers 
                and token.text.lower() == next_token.text.lower())
    
    def get_error(self, sentence: str):
        """
        Returns: (error_category, error_name, True/False)
        """
        doc = self.nlp(sentence)
        
        for i in range(len(doc) - 1):
            token = doc[i]
            next_token = doc[i+1]
            
            # Check for identical text (case-insensitive)
            if token.text.lower() == next_token.text.lower():
                
                # Ignore punctuation
                if token.is_punct:
                    continue
                
                # Check valid French repetitions
                if self._is_valid_reflexive(token, next_token):
                    continue
                    
                if self._is_valid_intensifier(token, next_token):
                    continue
                
                # Found invalid repetition
                return self.error_category, self.error_name, True
        
        return self.error_category, self.error_name, False
    
    def correct(self, sentence: str) -> str:
        """
        Removes redundant word while preserving spacing.
        """
        doc = self.nlp(sentence)
        tokens_to_keep = []
        
        i = 0
        while i < len(doc):
            token = doc[i]
            
            # Look ahead
            if i < len(doc) - 1:
                next_token = doc[i+1]
                
                # Check if this is an invalid repetition
                if (token.text.lower() == next_token.text.lower() 
                    and not token.is_punct 
                    and not self._is_valid_reflexive(token, next_token)
                    and not self._is_valid_intensifier(token, next_token)):
                    
                    # Skip the second token (keep first, remove second)
                    tokens_to_keep.append(token.text_with_ws)
                    i += 2  # Skip both, but we added the first
                    continue
            
            tokens_to_keep.append(token.text_with_ws)
            i += 1
        
        return "".join(tokens_to_keep).strip()