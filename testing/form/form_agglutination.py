from pathlib import Path
from detecterreur.form.form_agglutination import FormAgglutination

def main():
    # Initialize the detector
    fa = FormAgglutination()

    # robustly find the test file relative to this script
    current_dir = Path(__file__).parent
    file_path = current_dir / "form_agglutination.txt"

    with open(file_path, "r", encoding="utf-8") as f:
        sentences = [line.strip() for line in f if line.strip()]

    for s in sentences:
        # Unpack the triplet: (Category, ErrorName, Boolean)
        category, error_code, has_error = fa.get_error(s)
        
        print(f"Sentence: {s}")
        print(f"Has agglutination error? {has_error} | Code: {error_code} ({category})")

        if has_error:
            corrected = fa.correct(s)
            print(f"Corrected: {corrected}")

        print("-" * 60)

if __name__ == "__main__":
    main()