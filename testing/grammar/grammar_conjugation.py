from pathlib import Path
from detecterreur.grammar.grammar_agreement import GrammarAgreement

def main():
    ga = GrammarAgreement()

    # Calculate path relative to THIS script file
    # This points to: .../detecterreur/testing/grammaire/grammar_agreement.txt
    current_dir = Path(__file__).parent
    file_path = current_dir / "grammar_agreement.txt"

    with open(file_path, "r", encoding="utf-8") as f:
        sentences = [line.strip() for line in f if line.strip()]

    for s in sentences:
        # Unpack the triplet: (Category, ErrorName, Boolean)
        category, error_code, has_error = ga.get_error(s)
        
        print(f"Sentence: {s}")
        print(f"Has agreement error? {has_error} | Code: {error_code} ({category})")

        if has_error:
            corrected = ga.correct(s)
            print(f"Corrected: {corrected}")

        print("-" * 60)

if __name__ == "__main__":
    main()