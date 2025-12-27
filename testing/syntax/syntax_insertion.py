from pathlib import Path
from detecterreur.syntax.syntax_insertion import SyntaxInsertion

def main():
    sins = SyntaxInsertion()

    current_dir = Path(__file__).parent
    file_path = current_dir / "syntax_insertion.txt"

    with open(file_path, "r", encoding="utf-8") as f:
        sentences = [line.strip() for line in f if line.strip()]

    for s in sentences:
        cat, name, has_error = sins.get_error(s)
        
        print(f"Sentence: {s}")
        print(f"Has Insertion Error? {has_error} ({cat}: {name})")

        if has_error:
            corrected = sins.correct(s)
            print(f"Corrected: {corrected}")

        print("-" * 40)

if __name__ == "__main__":
    main()