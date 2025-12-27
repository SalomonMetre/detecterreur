import spacy
from spellchecker import SpellChecker

class Validator:
    _instance = None
    _nlp = None
    _spell = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Validator, cls).__new__(cls)
            try:
                # 1. Chargement de spaCy (léger)
                cls._nlp = spacy.load("fr_core_news_sm", disable=["parser", "ner", "lemmatizer", "textcat"])
                # 2. Chargement de pyspellchecker (fr)
                cls._spell = SpellChecker(language='fr')
            except OSError:
                raise ImportError("Please run: python -m spacy download fr_core_news_sm")
        return cls._instance

    def is_valid(self, word: str) -> bool:
        """
        Vérifie si un mot est valide en utilisant spaCy ET pyspellchecker.
        """
        word_clean = word.strip().lower()

        # 1. Filtre rapide (longueur et exceptions)
        if len(word_clean) < 2 and word_clean not in ["y", "a", "à"]:
            return False
            
        # 2. Test spaCy (Très rapide, basé sur le hash du vocabulaire)
        if not self._nlp.vocab[word_clean].is_oov:
            return True
        
        # 3. Test pyspellchecker (Plus complet pour les mots rares)
        # On utilise .known pour voir si le dictionnaire pur Python le reconnaît
        if word_clean in self._spell.known([word_clean]):
            return True
            
        return False