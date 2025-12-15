import pandas as pd
import numpy as np
import os
from sklearn.metrics.pairwise import cosine_similarity
from detecterreur.form.form_diacritic import FormDiacritic
from transformers import AutoModelForCausalLM, AutoTokenizer

def find_changed_word(original, corrected):
    """A simple diff logic to find the first changed word."""
    orig_words = original.split()
    corr_words = corrected.split()
    if len(orig_words) != len(corr_words):
        # Basic fallback if sentence structures are very different
        for word in orig_words:
            if word not in corr_words:
                return word
        return None

    for o, c in zip(orig_words, corr_words):
        if o != c:
            return o
    return None

# --- 1. CONFIGURATION AND DATA (Replace with your actual data source) ---

def setup_data_and_model():
    """Initializes detector, loads mock rules data, and sets up the LLM components."""
    
    # 1. Error Detection (Simulated for one sentence)
    dia = FormDiacritic()
    sentence = "Je suis francais"
    # Simulate getting the full correction from an advanced DetectErreur version
    corrected_sentence = "Je suis français"
    incorrect_word = find_changed_word(sentence, corrected_sentence)
    
    # get_error returns (has_error: bool, error_name: str)
    has_error, error_name = dia.get_error(sentence)
    
    if not has_error:
        print("No error detected. Exiting RAG process.")
        return None, None, None, None, None, None, None, None

    print(f"✅ Detected Error: {error_name} in sentence: '{sentence}'")

    # 2. Vector Store Setup (Loading rules to DataFrame)
    # Load from CSV and ensure column name is 'rules'
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
        return None, None, None, None, None, None, None, None

    rules_df['embeddings'] = rules_df['rules'].apply(lambda x: embedding_model.encode(x))

    # 3. LLM Setup
    model_name = "Qwen/Qwen2.5-1.5B-Instruct"
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(model_name)
    except Exception as e:
        print(f"Error loading Qwen model/tokenizer: {e}")
        return None, None, None, None, None, None, None, None
    
    # Set model to evaluation mode
    model.eval()
    
    return sentence, corrected_sentence, incorrect_word, error_name, rules_df, model, tokenizer, embedding_model

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

def generate_feedback(sentence, corrected_sentence, error_name, context, model, tokenizer):
    """Creates the final RAG prompt and generates the model's response."""
    
    # System prompt for the persona
    system_prompt = "Tu es un tuteur de français (FLE) qui explique une erreur de manière simple, pédagogique et encourageante."

    # User prompt with the specific task
    user_content = f"""### Tâche
Corrige l'erreur de type '{error_name}' dans la phrase de l'élève.

### Phrase de l'élève
Phrase de l'élève : "{sentence}"

### Phrase corrigée
"{corrected_sentence}"

### Contexte de la règle
{context}

### Consignes
1.  **Explique l'erreur** en te basant **uniquement** sur le "Contexte de la règle" fourni. Ne mentionne aucune autre règle.
2.  Sois bref, clair et encourageant.
3.  Termine ta réponse par une phrase complète.
4.  **Ne dépasse pas 200 mots.**

### Feedback pour l'élève :"""
    
    # Use the model's chat template to format the prompt correctly
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]
    inputs = tokenizer.apply_chat_template(
        messages,
        add_generation_prompt=True,
        tokenize=True,
        return_dict=True,
        return_tensors="pt",
    ).to(model.device)

    # Generate the output
    outputs = model.generate(**inputs, max_new_tokens=180, do_sample=True, temperature=0.4, top_p=0.9, repetition_penalty=1.15, eos_token_id=tokenizer.eos_token_id, pad_token_id=tokenizer.eos_token_id)
    
    # Decode the *newly generated* tokens only
    generated_text = tokenizer.decode(outputs[0][inputs["input_ids"].shape[-1]:], skip_special_tokens=True)
    
    return generated_text

# --- ENTRY POINT ---

if __name__ == "__main__":
    
    # Load all components
    sentence, corrected_sentence, incorrect_word, error_name, rules_df, model, tokenizer, embedding_model = setup_data_and_model()

    if rules_df is not None:
        # 1. Create the Query Text (incorporates error type and original sentence)
        query_text = f"Règle de la cédille 'ç' pour corriger le mot '{incorrect_word}'"
        
        # 2. Retrieve Context
        retrieved_context = retrieve_context(rules_df, query_text, embedding_model, top_k=2)
        
        # 3. Generate Final Feedback
        final_feedback = generate_feedback(sentence, corrected_sentence, error_name, retrieved_context, model, tokenizer)
        
        print("\n" + "="*60)
        print("🇫🇷 FINAL GENERATED FEEDBACK FOR FRENCH STUDENT 🇫🇷")
        print("="*60)
        print(final_feedback)
        print("="*60 + "\n")
