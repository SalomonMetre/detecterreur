from detecterreur.letter.letter_substitution import LetterSubstitution

def main():
    ls = LetterSubstitution(distance=2)

    # Read sentences from the file
    with open("testing/letter/letter_substitution.txt", "r", encoding="utf-8") as f:
        sentences = [line.strip() for line in f if line.strip()]

    for s in sentences:
        has_error, error_type = ls.get_error(s)
        print(f"Sentence: {s}")
        print(f"Has letter substitution error? {has_error}, Error type: {error_type}")

        if has_error:
            corrected = ls.correct(s)
            print(f"Corrected: {corrected}")

        print("-" * 40)

if __name__ == "__main__":
    main()
