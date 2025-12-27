from pathlib import Path
from detecterreur.grammar.grammar_euphonic import GrammarEuphonic

def main():
    geuf = GrammarEuphonic()

    # Test file path logic
    current_dir = Path(__file__).parent
    file_path = current_dir / "grammar_euphonic.txt"
    
    # Manual fallback if file doesn't exist yet for testing
    if not file_path.exists():
        sentences = [
            "A-il mangé ?",          # Error: A-t-il
            "Va-il venir ?",         # Error: Va-t-il
            "A-t-elle fini ?",       # Correct
            "Y a-t-il du pain ?",    # Correct
            "Parle-il ?"             # Error: Parle-t-il
        ]
    else:
        with open(file_path, "r", encoding="utf-8") as f:
            sentences = [line.strip() for line in f if line.strip()]

    for s in sentences:
        cat, name, has_error = geuf.get_error(s)
        
        print(f"Sentence: {s}")
        print(f"Has Euphonic Error? {has_error} | Code: {name} ({cat})")

        if has_error:
            corrected = geuf.correct(s)
            print(f"Corrected: {corrected}")

        print("-" * 60)

if __name__ == "__main__":
    main()