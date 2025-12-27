import spacy

class Validator:
    _instance = None
    _nlp = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Validator, cls).__new__(cls)
            try:
                # Load only the vocabulary for speed (no parser/ner needed)
                cls._nlp = spacy.load("fr_core_news_sm", disable=["parser", "ner", "lemmatizer", "textcat"])
            except OSError:
                raise ImportError("Please run: python -m spacy download fr_core_news_sm")
        return cls._instance

    def is_valid(self, word: str) -> bool:
        """
        Returns True if the word is a known, valid French word.
        """
        # 1. Ignore tiny words/punctuation (except specific valid ones)
        if len(word) < 2 and word.lower() not in ["y", "a", "à"]:
            return False
            
        # 2. Ask spaCy: Is this word in the French vocabulary?
        # is_oov = "Is Out Of Vocabulary"
        # If is_oov is False, the word is VALID.
        if not self._nlp.vocab[word].is_oov:
            return True
        
        # 3. Check lowercase version (handles "Cuisine" at start of sentence)
        if not self._nlp.vocab[word.lower()].is_oov:
            return True
            
        return False