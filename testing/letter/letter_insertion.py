from detecterreur.ortographe.letter_insertion import LetterInsertion

def main():
    li = LetterInsertion(distance=2)

    # Read sentences from the file
    with open("testing/letter/letter_insertion.txt", "r", encoding="utf-8") as f:
        sentences = [line.strip() for line in f if line.strip()]

    for s in sentences:
        has_error, error_type = li.get_error(s)
        print(f"Sentence: {s}")
        print(f"Has letter insertion error? {has_error} ({error_type})")

        if has_error:
            corrected = li.correct(s)
            print(f"Corrected: {corrected}")

        print("-" * 40)


if __name__ == "__main__":
    main()
