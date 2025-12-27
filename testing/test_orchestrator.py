import sys
from pathlib import Path
from typing import List, Union, Dict, Any
from detecterreur.orchestrator import Orchestrator

def run_test(source: Union[List[str], str]):
    """
    Runs the orchestrator on a source, which can be:
    1. A list of strings (sentences)
    2. A string (file path)
    """
    orc = Orchestrator()

    # 1. Load Sentences
    sentences = []
    if isinstance(source, list):
        print(f"\n[INFO] Testing on {len(source)} provided sentences.\n")
        sentences = source
    elif isinstance(source, str):
        path = Path(source)
        if not path.exists():
            print(f"[ERROR] File not found: {source}")
            return
        print(f"\n[INFO] Loading sentences from file: {source}\n")
        try:
            with open(path, "r", encoding="utf-8") as f:
                sentences = [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f"[ERROR] Failed to read file: {e}")
            return

    # 2. Process
    for i, s in enumerate(sentences, 1):
        print(f"--- Test #{i} -----------------------------------------------------------")
        print(f"Original:   {s}")

        # A. Get Errors (Detection Phase)
        errors = orc.get_error(s)
        detected_errors = [f"[{cat}] {name}" for cat, name, is_err in errors if is_err]

        print(f"Detected:   {', '.join(detected_errors) if detected_errors else 'None'}")

        # B. Correct (Correction Phase)
        correction = orc.correct(s)
        print(f"Correction: {correction}")

        # C. Get Detailed Report
        report = orc.get_detailed_report(s)
        print(f"Summary:    {report['summary']['total_errors']} errors found")
        print(f"Suggestions:\n{report['suggestions']}")
        print("")

def main():
    # Default test suite covering multiple layers
    default_sentences = [
        # 1. Agglutination + Conjugation
        "Les chat mangent dansle cuisine.",

        # 2. Punctuation + Euphonic
        "A il fini?",

        # 3. Spelling (Voting) + Syntax
        "Je vois le oeseau.",

        # another one
        "Toi et moi sont là."
    ]

    # Check command line args
    if len(sys.argv) > 1:
        # If file path provided
        run_test(sys.argv[1])
    else:
        # Run default
        run_test(default_sentences)

if __name__ == "__main__":
    main()
