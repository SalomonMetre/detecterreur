from detecterreur.form.form_case import FormCase

def main():
    fc = FormCase()

    # Read sentences from the file
    with open("testing/form/form_case.txt", "r", encoding="utf-8") as f:
        sentences = [line.strip() for line in f if line.strip()]

    for s in sentences:
        has_error, error_type = fc.get_error(s)
        print(f"Sentence: {s}")
        print(f"Has FMAJ error? {has_error}, Type: {error_type}")

        if has_error:
            corrected = fc.correct(s)
            print(f"Corrected: {corrected}")

        print("-" * 40)


if __name__ == "__main__":
    main()
