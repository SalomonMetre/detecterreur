from pathlib import Path
from detecterreur.letter.letter_substitution import LetterSubstitution

def main():
    ls = LetterSubstitution(distance=2)

    # Path to testing/letter/letter_substitution.txt
    current_dir = Path(__file__).parent
    file_path = current_dir / "letter_substitution.txt"

    with open(file_path, "r", encoding="utf-8") as f:
        sentences = [line.strip() for line in f if line.strip()]

    for s in sentences:
        error_category, error_name, has_error = ls.get_error(s)
        
        print(f"Sentence: {s}")
        print(f"Has substitution error? {has_error} ({error_category}: {error_name})")

        if has_error:
            corrected = ls.correct(s)
            print(f"Corrected: {corrected}")

        print("-" * 40)

if __name__ == "__main__":
    main()