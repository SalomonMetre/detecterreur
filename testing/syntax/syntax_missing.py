from pathlib import Path
from detecterreur.syntax.syntax_missing import SyntaxMissing

def main():
    smis = SyntaxMissing()

    current_dir = Path(__file__).parent
    file_path = current_dir / "syntax_missing.txt"

    with open(file_path, "r", encoding="utf-8") as f:
        sentences = [line.strip() for line in f if line.strip()]

    for s in sentences:
        cat, name, has_error = smis.get_error(s)
        
        print(f"Sentence: {s}")
        print(f"Has Missing Syntax? {has_error} ({cat}: {name})")

        if has_error:
            # Note: correct() here returns a suggestion string
            suggestion = smis.correct(s)
            print(f"Feedback: {suggestion}")

        print("-" * 40)

if __name__ == "__main__":
    main()