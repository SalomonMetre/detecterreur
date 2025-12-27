from pathlib import Path
from detecterreur.letter.letter_missing import LetterMissing

def main():
    lm = LetterMissing(distance=2)

    # Calculate the path relative to THIS script file
    # This points to: .../detecterreur/testing/letter/letter_missing.txt
    current_dir = Path(__file__).parent
    file_path = current_dir / "letter_missing.txt"

    with open(file_path, "r", encoding="utf-8") as f:
        sentences = [line.strip() for line in f if line.strip()]

    for s in sentences:
        # Unpack the triplet (Category, Name, Boolean)
        error_category, error_name, has_error = lm.get_error(s)
        
        print(f"Sentence: {s}")
        print(f"Has missing-letter error? {has_error} ({error_category}: {error_name})")

        if has_error:
            corrected = lm.correct(s)
            print(f"Corrected: {corrected}")

        print("-" * 40)

if __name__ == "__main__":
    main()