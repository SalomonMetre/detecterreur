from typing import List, Tuple, Dict, Optional, Any
import re

# --- 1. Form (Shape of words) ---
from detecterreur.form.form_agglutination import FormAgglutination
from detecterreur.form.form_case import FormCase
from detecterreur.form.form_diacritic import FormDiacritic

# --- 2. Punctuation ---
from detecterreur.punctuation.punctuation import Punctuation

# --- 3. Letter (Spelling) ---
from detecterreur.letter.letter_insertion import LetterInsertion
from detecterreur.letter.letter_missing import LetterMissing
from detecterreur.letter.letter_substitution import LetterSubstitution
from detecterreur.letter.letter_order import LetterOrder

# --- 4. Grammar (Morphology) ---
from detecterreur.grammar.grammar_conjugation import GrammarConjugation
from detecterreur.grammar.grammar_agreement import GrammarAgreement
from detecterreur.grammar.grammar_euphonic import GrammarEuphonic

# --- 5. Syntax (Sentence Structure) ---
from detecterreur.syntax.syntax_order import SyntaxOrder
from detecterreur.syntax.syntax_insertion import SyntaxInsertion
from detecterreur.syntax.syntax_missing import SyntaxMissing
from detecterreur.syntax.syntax_redundancy import SyntaxRedundancy

class Orchestrator:
    """
    Orchestrates the detection, correction, and suggestion of errors in French text.
    
    - correct(s): Cumulative correction (Pipeline).
    - get_suggestions(s): Atomic suggestions (Independent).
    """

    def __init__(self):
        """
        Initializes all detectors and sets up the pipeline.
        """
        self.detectors_map: Dict[str, Any] = {}

        # --- Instantiate Detectors ---
        self.punc = Punctuation()
        self.fmaj = FormCase()
        self.fagl = FormAgglutination()

        # Orthography
        self.fdia = FormDiacritic(distance=1)
        self.lins = LetterInsertion()
        self.lmis = LetterMissing()
        self.lsub = LetterSubstitution()
        self.lord = LetterOrder()

        # Syntax
        self.sred = SyntaxRedundancy()
        self.sord = SyntaxOrder()
        self.smis = SyntaxMissing()
        self.sins = SyntaxInsertion()

        # Grammar
        self.geuf = GrammarEuphonic()
        self.gacc = GrammarAgreement()
        self.gcon = GrammarConjugation()

        # Reporting Order (Logical grouping for UI / get_error return list)
        self.all_detectors = [
            self.fagl, self.sred,           # Structure Cleaning
            self.geuf, self.fmaj,           # Euphonics & Caps
            self.fdia, self.lins, self.lmis, self.lsub, self.lord,  # Ortho
            self.gacc, self.gcon,           # Grammar
            self.sord, self.smis, self.sins, # Deep Syntax
            self.punc                       # Final Polish
        ]

        for detector in self.all_detectors:
            self.detectors_map[detector.error_name] = detector
            self.detectors_map[detector.error_category] = detector

    # -------------------------------------------------------------------------
    # 1. GET ERROR
    # -------------------------------------------------------------------------

    def get_error(
        self,
        sentence: str,
        category: List[str] = [],
        error_names: List[str] = []
    ) -> List[Tuple[str, str, bool]]:
        """
        Detects errors in the sentence.
        Returns: List of (category, error_name, has_error)
        """
        results = []
        for detector in self.all_detectors:
            if category and detector.error_category not in category:
                continue
            if error_names and detector.error_name not in error_names:
                continue

            try:
                cat, name, has_err = detector.get_error(sentence)
                results.append((cat, name, has_err))
            except Exception as e:
                print(f"[WARN] Detector {detector.error_name} failed: {e}")
                results.append((detector.error_category, detector.error_name, False))
        return results

    # -------------------------------------------------------------------------
    # 2. CORRECT (CASCADED)
    # -------------------------------------------------------------------------

    def correct(
        self,
        sentence: str,
        category: List[str] = [],
        error_names: List[str] = []
    ) -> str:
        """
        Corrects errors in the sentence SEQUENTIALLY (Cascaded).
        The output of one detector becomes the input of the next.
        """
        current_text = sentence

        def should_run(detector: Any) -> bool:
            if category and detector.error_category not in category:
                return False
            if error_names and detector.error_name not in error_names:
                return False
            return True

        def apply_safe(detector: Any, text: str) -> str:
            if not should_run(detector):
                return text
            try:
                # Strictly check if error exists before correcting
                _, _, has_error = detector.get_error(text)
                if has_error:
                    return detector.correct(text)
            except Exception:
                # If a detector crashes, return text as is to preserve pipeline
                return text
            return text

        # --- Phase 1: Structure & Cleaning ---
        current_text = apply_safe(self.fagl, current_text)  # Fix "dansle"
        current_text = apply_safe(self.sred, current_text)  # Fix "je je"

        # --- Phase 2: Euphonics & Form ---
        current_text = apply_safe(self.geuf, current_text)  # Fix "A-t-il"
        current_text = apply_safe(self.fmaj, current_text)  # Fix "Capitalization"

        # --- Phase 3: Orthography ---
        ortho_pipeline = [self.fdia, self.lins, self.lmis, self.lsub, self.lord]
        for detector in ortho_pipeline:
            current_text = apply_safe(detector, current_text)

        # --- Phase 4: Grammar ---
        current_text = apply_safe(self.gacc, current_text)
        current_text = apply_safe(self.gcon, current_text)

        # --- Phase 5: Deep Syntax ---
        syntax_pipeline = [self.sord, self.smis, self.sins]
        for detector in syntax_pipeline:
            current_text = apply_safe(detector, current_text)

        # --- Phase 6: Punctuation (LAST) ---
        current_text = apply_safe(self.punc, current_text)

        return current_text

    # -------------------------------------------------------------------------
    # 3. GET SUGGESTIONS (INDEPENDENT)
    # -------------------------------------------------------------------------

    def get_suggestions(
        self,
        sentence: str,
        category: List[str] = [],
        error_names: List[str] = []
    ) -> List[Tuple[str, str, bool, str]]:
        """
        Returns suggestions for correcting errors INDEPENDENTLY.
        Each detector runs on the ORIGINAL sentence.
        
        Returns:
            List[Tuple[str, str, bool, str]]: (cat, name, has_err, suggested_text)
            If has_err is False, suggested_text is the original input.
        """
        results = []
        
        # We iterate through detectors in the defined reporting order
        for detector in self.all_detectors:
            # Apply Filters
            if category and detector.error_category not in category:
                continue
            if error_names and detector.error_name not in error_names:
                continue

            try:
                # 1. Detect on ORIGINAL sentence
                cat, name, has_err = detector.get_error(sentence)
                
                if has_err:
                    # 2. Independent Correction
                    # We apply this detector's fix to the ORIGINAL sentence.
                    # This isolates the change (e.g., FAGL only fixes "dansle", ignoring other errors).
                    suggestion = detector.correct(sentence)
                    results.append((cat, name, has_err, suggestion))
                else:
                    # No error -> Suggestion is the input itself
                    results.append((cat, name, has_err, sentence))

            except Exception as e:
                print(f"[WARN] Suggestion generation failed for {detector.error_name}: {e}")
                results.append((detector.error_category, detector.error_name, False, sentence))

        return results

    # -------------------------------------------------------------------------
    # 4. GET DETAILED REPORT
    # -------------------------------------------------------------------------

    def get_detailed_report(
        self,
        sentence: str,
        category: List[str] = [],
        error_names: List[str] = []
    ) -> Dict[str, Any]:
        """
        Generates a detailed report.
        - 'corrected': The final result of the cascaded pipeline.
        - 'suggestions': The independent suggestions per detector.
        """
        errors = self.get_error(sentence, category, error_names)
        
        # Cascaded Correction (Best Final Result)
        corrected_cascaded = self.correct(sentence, category, error_names)
        
        # Independent Suggestions (For UI/Debugging)
        suggestions = self.get_suggestions(sentence, category, error_names)

        return {
            "original": sentence,
            "corrected": corrected_cascaded,
            "errors": errors,
            "suggestions": suggestions,
            "summary": {
                "total_errors": sum(1 for _, _, has_err in errors if has_err),
                "corrected_sentence": corrected_cascaded,
            }
        }