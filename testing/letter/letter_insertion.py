from pathlib import Path
from detecterreur.letter.letter_insertion import LetterInsertion

def main():
    li = LetterInsertion(distance=2)

    # Calculate the path relative to THIS script file
    # This points to: .../detecterreur/testing/letter/letter_insertion.txt
    current_dir = Path(__file__).parent
    file_path = current_dir / "letter_insertion.txt"

    with open(file_path, "r", encoding="utf-8") as f:
        sentences = [line.strip() for line in f if line.strip()]

    for s in sentences:
        # Unpack the triplet (Category, Name, Boolean)
        error_category, error_name, has_error = li.get_error(s)
        
        print(f"Sentence: {s}")
        print(f"Has letter insertion error? {has_error} ({error_category}: {error_name})")

        if has_error:
            corrected = li.correct(s)
            print(f"Corrected: {corrected}")

        print("-" * 40)

if __name__ == "__main__":
    main()