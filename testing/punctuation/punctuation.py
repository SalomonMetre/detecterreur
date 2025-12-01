from detecterreur.punctuation.punctuation import Punctuation

def main():
    punc = Punctuation()

    # Read sentences from the file
    with open("testing/punctuation/punctuation.txt", "r", encoding="utf-8") as f:
        sentences = [line.strip() for line in f if line.strip()]

    for s in sentences:
        has_error, error_code = punc.get_error(s)
        print(f"Sentence: {s}")
        print(f"Has punctuation error? {has_error} | Code: {error_code}")

        if has_error:
            corrected = punc.correct(s)
            print(f"Corrected: {corrected}")

        print("-" * 60)

if __name__ == "__main__":
    main()
