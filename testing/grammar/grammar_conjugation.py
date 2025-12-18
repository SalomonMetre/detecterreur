from detecterreur.grammaire.grammar_conjugation import GrammarConjugation

def main():
    gc = GrammarConjugation()

    with open("testing/grammar/grammar_conjugation.txt", "r", encoding="utf-8") as f:
        sentences = [line.strip() for line in f if line.strip()]

    for s in sentences:
        has_error, error_code = gc.get_error(s)
        print(f"Sentence: {s}")
        print(f"Has conjugation error? {has_error} | Code: {error_code}")

        if has_error:
            corrected = gc.correct(s)
            print(f"Corrected: {corrected}")

        print("-" * 60)

if __name__ == "__main__":
    main()
