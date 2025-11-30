from detecterreur.letter.letter_insertion import LetterInsertion

def main():
    li = LetterInsertion(distance=2)

    # Read sentences from the file
    with open("testing/letter/sentences.txt", "r", encoding="utf-8") as f:
        sentences = [line.strip() for line in f if line.strip()]

    for s in sentences:
        has_error = li.has_insertion_error(s)
        print(f"Sentence: {s}")
        print(f"Has letter insertion error? {has_error}")

        if has_error:
            corrected = li.correct(s)  # use `correct`, not `fix_insertion_errors`
            print(f"Corrected: {corrected}")

        print("-" * 40)


if __name__ == "__main__":
    main()
