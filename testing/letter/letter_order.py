from detecterreur.letter.letter_order import LetterOrder

def main():
    lo = LetterOrder()

    # Read sentences from the file
    with open("testing/letter/letter_order.txt", "r", encoding="utf-8") as f:
        sentences = [line.strip() for line in f if line.strip()]

    for s in sentences:
        has_error = lo.has_order_error(s)
        print(f"Sentence: {s}")
        print(f"Has letter-order error? {has_error}")

        if has_error:
            corrected = lo.correct(s)
            print(f"Corrected: {corrected}")

        print("-" * 40)

if __name__ == "__main__":
    main()
