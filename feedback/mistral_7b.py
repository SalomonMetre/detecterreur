import os
from detecterreur.form.form_diacritic import FormDiacritic
import ollama
from codecarbon import EmissionsTracker

def load_error():
    """ Will not be present in the final version, its only purpose is to simulate DetectErreur."""
    # Initialize detector
    err = FormDiacritic()

    sentence = "Je suis francais"
    error = err.get_error(sentence)
    error_name = error[1]
    correction = err.correct(sentence)

    return sentence, error_name, correction



def find_changed_word(original, corrected):
    """ Finds the first changed word pair (incorrect, correct)."""
    orig_words = original.split()
    corr_words = corrected.split()
    
    # 1. Same length: direct comparison
    if len(orig_words) == len(corr_words):
        for o, c in zip(orig_words, corr_words):
            if o != c:
                return o, c
    
    # 2. Different length: naive fallback (just return incorrect word)
    for word in orig_words:
        if word not in corr_words:
            return word, None
            
    return None, None



def load_resources():
    """ Loads the resources needed for feedback generation. Returns:
    - The error detector
    """

    # Initialize detector
    err = FormDiacritic()

    return err

def generate_feedback_ollama(sentence, corrected_sentence, incorrect_word, corrected_word, model_name="mistral:7b-instruct"):
    """Creates the final RAG prompt and generates the model's response."""

    # Combined prompt (System + User) for better adherence with Mistral models
    prompt = f"""[INST] Tu es un assistant pédagogique expert en grammaire française.
Ton but est d'expliquer une correction à un élève de manière claire, précise et sans jargon technique.

Voici la correction à analyser :
- Phrase originale, donc le contexte où la faute se trouve : "{sentence}"
- Phrase corrigée : "{corrected_sentence}"
- Mot incorrect : "{incorrect_word}"
- Mot corrigé : "{corrected_word}"

Instructions :
1. Explique pourquoi "{incorrect_word}" a été corrigé en "{corrected_word}".
2. Réponds avec des phrases complètes et grammaticalement correctes en français.
3. Ne mentionne pas les codes d'erreur (ex: FDIA).
4. Sois concis (2 à 3 phrases).
5. Parfois la faute est relative seulement à l'ortographe, autres fois à la grammaire.


Explication : [/INST]"""

    messages = [
        {"role": "user", "content": prompt}
    ]
    
    try:
        response = ollama.chat(
            model=model_name,
            messages=messages,
            options={
                'temperature': 0.1,
            }
        )
        generated_explanation = response['message']['content']
    except Exception as e:
        raise RuntimeError(f"Failed to get response from Ollama: {e}")

    return generated_explanation

def process_request(sentence, corrected_sentence, err):
    """
    USER REQUEST: Processes a single input sentence.
    """
    # Identify the specific word change
    incorrect_word, corrected_word_val = find_changed_word(sentence, corrected_sentence)
    
    # Detect Error Type
    has_error, error_name = err.get_error(sentence)
    
    if not has_error and not incorrect_word:
        return "Aucune erreur détectée."
    
    # Generate Feedback
    explanation = generate_feedback_ollama(
        sentence, corrected_sentence, incorrect_word, corrected_word_val, model_name="mistral:7b-instruct"
    )
    return explanation

if __name__ == "__main__":

    # Set output_dir to project root so it always appends to the same emissions.csv
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tracker = EmissionsTracker(output_dir=project_root)
    tracker.start()

    try:
        err = load_resources()
        # Use load_error to simulate input
        sentence, error_name, correction = load_error()
        
        print("\n" + "="*60)
        print(f"Processing: '{sentence}' -> '{correction}'")
        print("="*60)
        
        final_response = process_request(sentence, correction, err)
        print(f"\nGenerated Feedback:\n{final_response}")
    finally:
        tracker.stop()
