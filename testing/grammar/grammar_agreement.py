from detecterreur.grammar.grammar_agreement import GrammarAgreement

def main():
    ga = GrammarAgreement()

    with open("testing/grammar/grammar_agreement.txt", "r", encoding="utf-8") as f:
        sentences = [line.strip() for line in f if line.strip()]

    for s in sentences:
        has_error, error_code = ga.get_error(s)
        print(f"Sentence: {s}")
        print(f"Has agreement error? {has_error} | Code: {error_code}")

        if has_error:
            corrected = ga.correct(s)
            print(f"Corrected: {corrected}")

        print("-" * 60)

if __name__ == "__main__":
    main()