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
    """ Loads the resources needed for Retrieval Augmented Generation. Returns:
    - The error detector
    - The rules dataframe
    - The embedding model
    """

    # Initialize detector
    err = FormDiacritic()
    
    # Load rules
    script_dir = os.path.dirname(os.path.abspath(__file__))
    df = pd.read_csv(os.path.join(script_dir, 'rules', 'rules_test2.csv'))
    df.rename(columns={'rules,': 'rules'}, inplace=True)

    # Load embedding model
    try:
        embedding_model = SentenceTransformer('dangvantuan/sentence-camembert-base')
    except ImportError:
        print("Error: sentence-transformers is not installed.")
        embedding_model = None

    # Compute embeddings for the rules and add them as a column in the df
    if embedding_model is not None and 'rules' in df.columns:
        df['embeddings'] = df['rules'].apply(lambda x: embedding_model.encode(x))

    # print("All resources loaded successfully.")
    return err, df, embedding_model

def retrieve_context(df, prompt_text, embedding_model, top_k=5):
    
    # Embed query/prompt for finding the similarity
    prompt_embedding = embedding_model.encode(prompt_text)

    # Calculate similarity
    all_embeddings = np.vstack(df['embeddings'].values)
    similarities = cosine_similarity(prompt_embedding.reshape(1, -1), all_embeddings)[0]
    df['distance'] = similarities

    # Retrieve top k results
    top_k_results = df.sort_values(by='distance', ascending=False).head(top_k)

    # Format for the language model
    context = "\n".join(top_k_results['rules'].tolist())

    print(f"Retrieved {top_k} relevant rules (top distance: {top_k_results['distance'].iloc[0]:.4f}).")
    return context

def generate_feedback_ollama(sentence, corrected_sentence, incorrect_word, corrected_word, context, model_name="ministral-3:3b"):
    """Creates the final RAG prompt and generates the model's response."""

    # Combined prompt (System + User) for better adherence with Mistral models
    prompt = f"""[INST] Tu es un assistant pédagogique expert en grammaire française.
Ton but est d'expliquer une correction à un élève de manière claire, précise et sans jargon technique.

Voici les règles de grammaire disponibles (Contexte) :
{context}

Voici la correction à analyser :
- Phrase originale : "{sentence}"
- Phrase corrigée : "{corrected_sentence}"
- Mot incorrect : "{incorrect_word}"
- Mot corrigé : "{corrected_word}"

Instructions :
1. Utilise la règle pertinente du contexte pour expliquer pourquoi "{incorrect_word}" a été corrigé en "{corrected_word}".
2. Si aucune règle ne correspond, explique la correction de manière factuelle.
3. Réponds avec des phrases complètes et grammaticalement correctes en français.
4. Ne mentionne pas les codes d'erreur (ex: FDIA).
5. Sois concis (2 à 3 phrases).

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

def process_request(sentence, corrected_sentence, err, rules_df, embedding_model):
    """
    USER REQUEST: Processes a single input sentence.
    """
    # Identify the specific word change
    incorrect_word, corrected_word_val = find_changed_word(sentence, corrected_sentence)
    
    # Detect Error Type
    has_error, error_name = err.get_error(sentence)
    
    if not has_error and not incorrect_word:
        return "Aucune erreur détectée."

    # Create RAG Query (embedded)
    query_text = f"Règle pour corriger '{incorrect_word}' en '{corrected_word_val}'. Erreur : {error_name}"
    print(f"Query: {query_text}")
    
    # Retrieve Context
    retrieved_context = retrieve_context(rules_df, query_text, embedding_model, top_k=5)
    
    # Generate Feedback
    explanation = generate_feedback_ollama(
        sentence, corrected_sentence, incorrect_word, corrected_word_val, retrieved_context, model_name="ministral-3:3b"
    )
    return explanation

if __name__ == "__main__":

    # Set output_dir to project root so it always appends to the same emissions.csv
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tracker = EmissionsTracker(output_dir=project_root)
    tracker.start()

    try:
        err, df, embedding_model = load_resources()
        # Use load_error to simulate input
        sentence, error_name, correction = load_error()
        
        print("\n" + "="*60)
        print(f"Processing: '{sentence}' -> '{correction}'")
        print("="*60)
        
        final_response = process_request(sentence, correction, err, df, embedding_model)
        print(f"\nGenerated Feedback:\n{final_response}")
    finally:
        tracker.stop()
