import re

class GrammarEuphonic:
    """
    Detects missing euphonic markers in French inversion questions using robust Regex.
    
    Catches collisions like:
    1. "A il" or "A-il"       -> "A-t-il" (Vowel-Vowel collision)
    2. "Vient il"             -> "Vient-il" (Missing hyphen)
    
    Category: GRAMMAIRE
    Error: GEUF
    """
    error_name = "GEUF"
    error_category = "GRAMMAIRE"

    def __init__(self):
        # Target pronouns for inversion
        pronouns = r"(?:il|elle|on|ils|elles|iel)"
        
        # -------------------------------------------------------------------------
        # Pattern 1: Vowel Collision (Needs -t-)
        # -------------------------------------------------------------------------
        # Detects: [Word ending in Vowel] + [Space or Hyphen] + [Pronoun starting with Vowel]
        # Examples: "Parle elle", "Parle-elle", "Va on", "Va-on"
        # Excludes: "Parle-t-elle" (already has -t-)
        #
        # Group 1: Verb (ending in vowel)
        # Group 2: Separator (space, hyphen, or space-hyphen-space)
        # Group 3: Pronoun
        self.pattern_vowel_collision = re.compile(
            r"\b([a-zA-Zà-ü]+[aeiouyàâéèêëîïôùûü])(\s*-\s*|\s+)(%s)\b" % pronouns,
            re.IGNORECASE | re.UNICODE
        )

        # -------------------------------------------------------------------------
        # Pattern 2: Missing Hyphen (Needs -)
        # -------------------------------------------------------------------------
        # Detects: [Word ending in T or D] + [Space] + [Pronoun]
        # Examples: "Vient il", "Prend elle"
        # Excludes: "Vient-il" (already has hyphen)
        #
        # Group 1: Verb (ending in t or d)
        # Group 2: Pronoun
        self.pattern_missing_hyphen = re.compile(
            r"\b([a-zA-Zà-ü]+[td])\s+(%s)\b" % pronouns,
            re.IGNORECASE | re.UNICODE
        )

    # -----------------------------------------------------
    # Public API
    # -----------------------------------------------------
    def get_error(self, sentence: str):
        """
        Returns: (error_category, error_name, True/False)
        """
        # Check Pattern 1 (Need -t-)
        if self.pattern_vowel_collision.search(sentence):
            return self.error_category, self.error_name, True

        # Check Pattern 2 (Need -)
        if self.pattern_missing_hyphen.search(sentence):
            return self.error_category, self.error_name, True
                    
        return self.error_category, self.error_name, False

    def correct(self, sentence: str) -> str:
        """
        Applies regex substitution to insert -t- or - where needed.
        """
        corrected = sentence
        
        # Fix 1: Insert -t- for vowel collisions
        # "Parle elle" -> "Parle-t-elle"
        # "Parle-elle" -> "Parle-t-elle"
        # We replace the bad separator (Group 2) with "-t-"
        corrected = self.pattern_vowel_collision.sub(r"\1-t-\3", corrected)
        
        # Fix 2: Insert - for missing hyphens
        # "Vient il" -> "Vient-il"
        corrected = self.pattern_missing_hyphen.sub(r"\1-\2", corrected)
        
        return corrected