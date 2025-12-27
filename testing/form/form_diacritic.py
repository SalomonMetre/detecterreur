from pathlib import Path
from detecterreur.form.form_diacritic import FormDiacritic

def main():
    # distance=2 allows correcting words with multiple missing accents 
    # e.g., "eleve" -> "élève" (2 changes)
    fd = FormDiacritic(distance=2)

    # Calculate path relative to THIS script file
    # This points to: .../detecterreur/testing/forme/form_diacritic.txt
    current_dir = Path(__file__).parent
    file_path = current_dir / "form_diacritic.txt"

    with open(file_path, "r", encoding="utf-8") as f:
        sentences = [line.strip() for line in f if line.strip()]

    for s in sentences:
        # Unpack the triplet: (Category, ErrorName, Boolean)
        category, error_name, has_error = fd.get_error(s)
        
        print(f"Sentence: {s}")
        print(f"Has form-diacritic error? {has_error} | Code: {error_name} ({category})")

        if has_error:
            corrected = fd.correct(s)
            print(f"Corrected: {corrected}")

        print("-" * 40)

if __name__ == "__main__":
    main()