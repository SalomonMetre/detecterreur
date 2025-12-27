from detecterreur.orchestrator import Orchestrator

# 1. Init
orch = Orchestrator()
input_sentence = "Je vas mal."

# 2. Get Layered Suggestions (List of tuples)
suggestions = orch.get_suggestions(input_sentence)

# 3. Print exactly as requested: CATEGORY SPACE NAME:BOOL:TEXT
for cat, name, has_err, text in suggestions:
    print(f"{cat} {name}:{has_err}:{text}")

# 4. Final Correction
print("\nFinal Correction:")
print(orch.correct(input_sentence))