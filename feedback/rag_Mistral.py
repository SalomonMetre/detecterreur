import pandas as pd
import numpy as np
import os
import torch
from sklearn.metrics.pairwise import cosine_similarity
from detecterreur.form.form_diacritic import FormDiacritic
import ollama
from codecarbon import EmissionsTracker
from sentence_transformers import SentenceTransformer

def load_error():
    # Initialize detector
    dia = FormDiacritic()

    sentence = "Je suis francais"
    error = dia.get_error(sentence)
    error_name = error[1]
    correction = dia.correct(sentence)

    return sentence, error_name, correction



def load_resources():

    # Load rules
    script_dir = os.path.dirname(os.path.abspath(__file__))
    df = pd.read_csv(os.path.join(script_dir, 'rules', 'rules_test2.csv'))
    df.rename(columns={'rules,': 'rules'}, inplace=True)

    # Load embedding model
    try:
        embedding_model = SentenceTransformer('dangvantuan/sentence-camembert-base')
    except ImportError:
        embedding_model = None

    # Pre-compute embeddings for rules to enable retrieval
    if embedding_model is not None and 'rules' in df.columns:
        df['embeddings'] = df['rules'].apply(lambda x: embedding_model.encode(x))

    # With Ollama, we don't load the model and tokenizer in the script.
    # The model is served by the Ollama application.
    return df, embedding_model

def retrieve_context(df, prompt_text, embedding_model, top_k=5):
    
    # Embed query/prompt
    prompt_embedding = embedding_model.encode(prompt_text)

    # Calculate similarity
    df['distance'] = df['embeddings'].apply(lambda x: np.dot(x, prompt_embedding))

    # Retrieve top k results
    top_k_results = df.sort_values(by='distance', ascending=False).head(top_k)

    # Format for the language model
    context = "\n".join(top_k_results['rules'].tolist())

    print(f"""Retrieved: {context}""")
    return context

def build_prompt(error_name, context, sentence, correction):
    SYSTEM_INSTRUCTION = (
        "Tu es un assistant pour des étudiants de Français. "
        "Explique brièvement et clairement l'erreur dans un court échantillon de texte. "
        "Utilise uniquement le français. "
        "Réponds en phrases complètes, concises et grammaticalement correctes."
    )

    USER_TEMPLATE = (
        "Type d'erreur : {error_type}\n"
        "Règles de grammaire (Contexte) : {error_context}\n"
        "Phrase avec erreur : {error_text}\n"
        "Correction proposée : {corrected_error}\n"
        "\nExplique l'erreur en utilisant le contexte fourni."
    )

    user_content = USER_TEMPLATE.format(
        error_type=error_name,
        error_context=context,
        error_text=sentence,
        corrected_error=correction,
    )

    return [
        {"role": "system", "content": SYSTEM_INSTRUCTION},
        {"role": "user", "content": user_content}
    ]



def generate_feedback_ollama(
    error_type: str,
    sentence: str,
    correction: str,
    context: str,
    model_name: str = "ministral-3:3b",
    temperature: float = 0.1
):
    
    # build_prompt returns messages in the format Ollama expects
    messages = build_prompt(error_type, context, sentence, correction)
    
    try:
        response = ollama.chat(
            model=model_name,
            messages=messages,
            options={
                'temperature': temperature,
            }
        )
        answer = response['message']['content']
    except Exception as e:
        raise RuntimeError(f"Failed to get response from Ollama: {e}")

    # Final guard: if the model returns something degenerate, fail loudly
    if not answer or answer == ".":
        raise RuntimeError("La génération a échoué ou est vide. Réessayez ou augmentez max_new_tokens.")

    return answer 

if __name__ == "__main__":
    # Set output_dir to project root so it always appends to the same emissions.csv
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tracker = EmissionsTracker(output_dir=project_root)
    tracker.start()

    try:
        df, embedding_model = load_resources()
        sentence, error_name, correction = load_error()
        
        # Retrieve context based on the error
        context = retrieve_context(df, f"{error_name} {sentence}", embedding_model)
        
        feedback = generate_feedback_ollama(
            error_name, sentence, correction, context, model_name="ministral-3:3b"
        )
        print(f"\nGenerated Feedback:\n{feedback}")
    finally:
        tracker.stop()

    
