from detecterreur.letter.letter_replacement import LetterReplacement

def main():
    lr = LetterReplacement(distance=2)

    # Read sentences from the file
    with open("testing/letter/letter_replacement.txt", "r", encoding="utf-8") as f:
        sentences = [line.strip() for line in f if line.strip()]

    for s in sentences:
        has_error = lr.has_replacement_error(s)
        print(f"Sentence: {s}")
        print(f"Has letter replacement error? {has_error}")

        if has_error:
            corrected = lr.correct(s)
            print(f"Corrected: {corrected}")

        print("-" * 40)

if __name__ == "__main__":
    main()