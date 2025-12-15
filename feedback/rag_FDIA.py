import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from detecterreur.forme.form_diacritic import FormDiacritic
from transformers import AutoModelForCausalLM, AutoTokenizer
from detecterreur.forme.form_diacritic import FormDiacritic

# --- 1. CONFIGURATION AND DATA (Replace with your actual data source) ---

# Mock CSV content based on your Colab output structure
MOCK_RULES_CSV_CONTENT = """rules,
FORME FDIA les rectifications de l'orthographe de 1990 préconisent la suppression de l'accent circonflexe sur le u et le i. Exemples : la chaine – la voute – paraitre – il parait,
FORME FDIA les mots en -ère et -ès prennent un accent grave : Une ère, un ers (légume lentille),
FORME FDIA on ne met jamais d’accent grave sur les voyelles « e » précédant un « x ». Exemples : un accent circonflexe, le sexe.,
FORME FDIA On utilise un accent aigu lorsque la voyelle « e » est la première lettre du mot Exemples : étable, élection, étendre…,\n
# ... (rest of the rules)
"""

def setup_data_and_model():
    """Initializes detector, loads mock rules data, and sets up the LLM components."""
    
    # 1. Error Detection (Simulated for one sentence)
    dia = FormDiacritic()
    sentence = "Je suis francais"
    
    # get_error returns (has_error: bool, error_name: str)
    has_error, error_name = dia.get_error(sentence)
    
    if not has_error:
        print("No error detected. Exiting RAG process.")
        return None, None, None, None

    print(f"✅ Detected Error: {error_name} in sentence: '{sentence}'")

    # 2. Vector Store Setup (MOCK: Loading rules to DataFrame)
    # In a real system, you would load this from your vector database index
    # Simulating pandas read_csv from string, assuming 'rules,' is the column name
    rules_df = pd.read_csv('rules.csv', sep=",")

    # Load embedding model (must be the same one used for embedding the rules initially)
    # Using a French-specific Sentence-Transformer model
    try:
        from sentence_transformers import SentenceTransformer
        embedding_model = SentenceTransformer('dangvantuan/sentence-camembert-base')
    except ImportError:
        print("Error: sentence-transformers is not installed. Please run: pip install sentence-transformers")
        return None, None, None, None

    rules_df['embeddings'] = rules_df['rules,'].apply(lambda x: embedding_model.encode(x))

    # 3. LLM Setup
    model_name = "Qwen/Qwen2.5-1.5B"
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(model_name)
    except Exception as e:
        print(f"Error loading Qwen model/tokenizer: {e}")
        return None, None, None, None
    
    # Set model to evaluation mode
    model.eval()
    
    return sentence, error_name, rules_df, model, tokenizer, embedding_model

# --- 2. RAG RETRIEVAL LOGIC ---

def retrieve_context(df, prompt_text, embedding_model, top_k=5):
    """Encodes the prompt and finds the top_k most similar rules (highest dot product)."""
    
    # 1. Embed the query/prompt
    prompt_embedding = embedding_model.encode(prompt_text)
    
    # 2. Calculate Similarity (Dot product = Unnormalized Cosine Similarity for normalized vectors)
    # Calculate dot product using NumPy or custom function
    # Note: df['embeddings'] elements are numpy arrays, this operation is efficient
    df['distance'] = df['embeddings'].apply(lambda x: np.dot(x, prompt_embedding))

    # 3. Retrieve Top K results
    top_k_results = df.sort_values('distance', ascending=False).head(top_k)
    
    # 4. Format context for the LLM
    context = "\n".join(top_k_results['rules,'].tolist())
    
    print(f"🔍 Retrieved {top_k} relevant rules (top distance: {top_k_results['distance'].iloc[0]:.4f}).")
    return context

# --- 3. GENERATION AND MAIN EXECUTION ---

def generate_feedback(sentence, error_name, context, model, tokenizer):
    """Creates the final RAG prompt and generates the model's response."""
    
    # RAG PROMPT (The highly refined instruction template from your Colab)
    rag_prompt = f"""En tant que tuteur de FLE (Français Langue Étrangère), votre rôle est de fournir un retour pédagogique clair, encourageant et utile à un.e étudiant.e qui vient de faire une erreur. L'erreur spécifique est la suivante : {error_name}, détectée dans la phrase : '{sentence}'.

Votre réponse doit impérativement :
- Reformuler les informations du 'Contexte' ci-dessous dans vos propres mots, en évitant toute copie directe.
- Expliquer la règle de manière simple et accessible.
- Donner des conseils pratiques pour éviter cette erreur à l'avenir.
- Inclure un ou deux exemples clairs, si pertinent, pour illustrer la correction.
- Maintenir un ton encourageant et constructif.
- Proposer une correction directe pour la phrase originale.

Le tout doit être concis et ne pas dépasser 200 mots.

Contexte :
{context}

Correction et explication :
"""
    
    # Use the model's chat template to format the prompt correctly
    messages = [{"role": "user", "content": rag_prompt}]
    inputs = tokenizer.apply_chat_template(
        messages,
        add_generation_prompt=True,
        tokenize=True,
        return_dict=True,
        return_tensors="pt",
    ).to(model.device)

    # Generate the output
    outputs = model.generate(**inputs, max_new_tokens=200, do_sample=True, temperature=0.7)
    
    # Decode the *newly generated* tokens only
    generated_text = tokenizer.decode(outputs[0][inputs["input_ids"].shape[-1]:], skip_special_tokens=True)
    
    return generated_text

# --- ENTRY POINT ---

if __name__ == "__main__":
    
    # Load all components
    sentence, error_name, rules_df, model, tokenizer, embedding_model = setup_data_and_model()

    if rules_df is not None:
        # 1. Create the Query Text (incorporates error type and original sentence)
        query_text = f"Explication de l'erreur FDIA (diacritique) dans la phrase '{sentence}'."
        
        # 2. Retrieve Context
        retrieved_context = retrieve_context(rules_df, query_text, embedding_model, top_k=5)
        
        # 3. Generate Final Feedback
        final_feedback = generate_feedback(sentence, error_name, retrieved_context, model, tokenizer)
        
        print("\n" + "="*60)
        print("🇫🇷 FINAL GENERATED FEEDBACK FOR FRENCH STUDENT 🇫🇷")
        print("="*60)
        print(final_feedback)
        print("="*60 + "\n")

