import pandas as pd
import numpy as np
import os
import torch
from sklearn.metrics.pairwise import cosine_similarity
from detecterreur.form.form_diacritic import FormDiacritic
import ollama
from codecarbon import EmissionsTracker

def find_changed_word(original, corrected):
    """A simple diff logic to find the first changed word pair (incorrect, correct)."""
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

# --- 1. CONFIGURATION AND DATA (Replace with your actual data source) ---

def load_resources():
    """
    SERVER STARTUP: Loads all heavy models and data ONCE.
    In a web app, this runs only when the server starts.
    """
    print("⏳ Loading models and rules database... (This may take a moment)")
    
    # 1. Initialize Detector
    dia = FormDiacritic()
    
    # Use absolute path relative to script location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    rules_df = pd.read_csv(os.path.join(script_dir, 'rules', 'rules_test2.csv'))
    rules_df.rename(columns={'rules,': 'rules'}, inplace=True)

    # Load embedding model (must be the same one used for embedding the rules initially)
    # Using a French-specific Sentence-Transformer model
    try:
        from sentence_transformers import SentenceTransformer
        embedding_model = SentenceTransformer('dangvantuan/sentence-camembert-base')
    except ImportError:
        print("Error: sentence-transformers is not installed. Please run: pip install sentence-transformers")
        return None

    rules_df['embeddings'] = rules_df['rules'].apply(lambda x: embedding_model.encode(x))

    # With Ollama, the model is served by a separate application,
    # so we don't need to load it in the script.
    
    print("✅ All resources loaded successfully.")
    return dia, rules_df, embedding_model

# --- 2. RAG RETRIEVAL LOGIC ---

def retrieve_context(df, prompt_text, embedding_model, top_k=5):
    """Encodes the prompt and finds the top_k most similar rules (highest dot product)."""
    
    # 1. Embed the query/prompt
    prompt_embedding = embedding_model.encode(prompt_text)
    
    # 2. Calculate Similarity (Dot product = Unnormalized Cosine Similarity for normalized vectors)
    df['distance'] = df['embeddings'].apply(lambda x: np.dot(x, prompt_embedding))

    # 3. Retrieve Top K results
    top_k_results = df.sort_values('distance', ascending=False).head(top_k)
    
    # 4. Format context for the LLM
    context = "\n".join(top_k_results['rules'].tolist())
    
    print(f"🔍 Retrieved {top_k} relevant rules (top distance: {top_k_results['distance'].iloc[0]:.4f}).")
    return context

# --- 3. GENERATION AND MAIN EXECUTION ---

def generate_feedback_ollama(sentence, corrected_sentence, incorrect_word, corrected_word, context, model_name="ministral-3:3b"):
    """Creates the final RAG prompt and generates the model's response."""
    
    # System prompt for the persona
    system_prompt = (
        "Tu es un assistant pédagogique expert en grammaire française. "
        "Ton but est d'expliquer une correction à un élève de manière claire, précise et sans jargon technique."
    )

    # User prompt with the specific task
    user_content = f"""### Tâche
Expliquer une correction orthographique à un élève.

### Correction à analyser
- Mot incorrect : "{incorrect_word}"
- Mot corrigé : "{corrected_word}"
- Phrase complète : "{corrected_sentence}"

### Règles de grammaire disponibles (Contexte)
{context}

### Instructions
1. **Filtrage** : Ignore les règles du contexte qui ne concernent pas la modification spécifique de "{incorrect_word}" en "{corrected_word}".
2. **Explication** : Utilise la règle pertinente pour expliquer l'erreur. Si aucune règle ne correspond exactement, décris simplement la correction de manière factuelle.
3. **Format** :
   - Réponse courte (2 à 3 phrases).
   - Ton neutre.
   - Ne mentionne JAMAIS les codes d'erreur (ex: FDIA).

### Réponse :"""
    
    # Use the model's chat template to format the prompt correctly
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]

    try:
        response = ollama.chat(
            model=model_name,
            messages=messages,
        )
        generated_text = response['message']['content']
    except Exception as e:
        raise RuntimeError(f"Failed to get response from Ollama: {e}")
    
    return generated_text

def process_request(sentence, corrected_sentence, dia, rules_df, embedding_model):
    """
    USER REQUEST: Processes a single input sentence.
    This is what runs every time a user clicks 'Check'.
    """
    # 1. Identify the specific word change
    incorrect_word, corrected_word_val = find_changed_word(sentence, corrected_sentence)
    
    # 2. Detect Error Type
    has_error, error_name = dia.get_error(sentence)
    
    if not has_error:
        return "Aucune erreur détectée."

    # 3. Create RAG Query
    query_text = f"Règle pour corriger '{incorrect_word}' en '{corrected_word_val}'. Erreur : {error_name}"
    print(f"🔎 Query: {query_text}")
    
    # 4. Retrieve Context
    retrieved_context = retrieve_context(rules_df, query_text, embedding_model, top_k=5)
    
    # 5. Generate Feedback
    # The original model was `mistralai/Ministral-3B-Instruct-2410`.
    # Ensure you have a corresponding model pulled in Ollama. We'll use `ministral-3:3b` as an example.
    feedback = generate_feedback_ollama(
        sentence, corrected_sentence, incorrect_word, corrected_word_val, retrieved_context, model_name="ministral-3:3b"
    )
    return feedback

# --- ENTRY POINT ---

if __name__ == "__main__":
    # Set output_dir to project root so it always appends to the same emissions.csv
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tracker = EmissionsTracker(output_dir=project_root)
    tracker.start()
    
    try:
        # 1. Server Startup (Load once)
        resources = load_resources()
        
        if resources:
            # 2. Simulate a User Request
            user_sentence = "Je suis francais"
            correction = "Je suis français"
            
            print("\n" + "="*60)
            print(f"📝 Processing: {user_sentence}")
            print("="*60)
            
            final_feedback = process_request(user_sentence, correction, *resources)
            
            print("\n🤖 FEEDBACK:\n" + final_feedback + "\n")
    finally:
        tracker.stop()
