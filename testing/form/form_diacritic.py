from detecterreur.forme.form_diacritic import FormDiacritic

def main():
    fd = FormDiacritic(distance=2)

    with open("testing/form/form_diacritic.txt", "r", encoding="utf-8") as f:
        sentences = [line.strip() for line in f if line.strip()]

    for s in sentences:
        has_error, error_type = fd.get_error(s)
        print(f"Sentence: {s}")
        print(f"Has form-diacritic error? {has_error} ({error_type})")

        if has_error:
            corrected = fd.correct(s)
            print(f"Corrected: {corrected}")

        print("-" * 40)

if __name__ == "__main__":
    main()
