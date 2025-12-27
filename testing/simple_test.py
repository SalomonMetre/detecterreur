# import orchestrator

from detecterreur.orchestrator import Orchestrator

orch = Orchestrator()
input_sentence = "Je vas mal."

# get suggestions
suggestions = orch.get_suggestions(input_sentence)
for suggestion in suggestions:
    print(f"{suggestion[0]} {suggestion[1]}:{suggestion[2]}:{suggestion[3]}")

# proposed correction
correction = orch.correct(input_sentence)
print(correction)