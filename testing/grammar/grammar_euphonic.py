from detecterreur.grammaire.grammar_euphonic import GrammarEuphonic

def main():
    geuf = GrammarEuphonic()

    # Read test sentences
    with open("testing/grammar/grammar_euphonic.txt", "r", encoding="utf-8") as f:
        sentences = [line.strip() for line in f if line.strip()]

    for s in sentences:
        has_error, error_code = geuf.get_error(s)
        print(f"Sentence: {s}")
        print(f"Has euphonics error? {has_error} | Code: {error_code}")

        if has_error:
            corrected = geuf.correct(s)
            print(f"Corrected: {corrected}")

        print("-" * 50)

if __name__ == "__main__":
    main()