from detecterreur.forme.form_agglutination import FormAgglutination

def main():
    fa = FormAgglutination(distance=2)

    with open("testing/form/form_agglutination.txt", "r", encoding="utf-8") as f:
        sentences = [line.strip() for line in f if line.strip()]

    for s in sentences:
        has_error, error_code = fa.get_error(s)
        print(f"Sentence: {s}")
        print(f"Has agglutination error? {has_error} | Code: {error_code}")

        if has_error:
            corrected = fa.correct(s)
            print(f"Corrected: {corrected}")

        print("-" * 60)

if __name__ == "__main__":
    main()
