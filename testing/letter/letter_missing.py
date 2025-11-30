from detecterreur.letter.letter_missing import LetterMissing

def main():
    lm = LetterMissing(distance=2)

    # Read sentences from the file
    with open("testing/letter/letter_missing.txt", "r", encoding="utf-8") as f:
        sentences = [line.strip() for line in f if line.strip()]

    for s in sentences:
        has_error = lm.has_missing_letter_error(s)
        print(f"Sentence: {s}")
        print(f"Has missing-letter error? {has_error}")

        if has_error:
            corrected = lm.correct(s)
            print(f"Corrected: {corrected}")

        print("-" * 40)

if __name__ == "__main__":
    main()
