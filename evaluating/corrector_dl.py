from transformers import pipeline
import os
import re
import xml.etree.ElementTree as ET
import difflib
from codecarbon import EmissionsTracker
from prettytable import PrettyTable

def load_resources():
    # Load model from Hugging Face
    corrector = pipeline(
        "text2text-generation",
        model="PoloHuggingface/French_grammar_error_corrector"
    )

    # Load gold data
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, 'reference.xml')

    with open(file_path, 'r', encoding='utf-8') as f:
        gold_corpus = f.read()

    return corrector, gold_corpus

def tokenize(text):
    # Simple tokenizer that keeps words and punctuation
    return re.findall(r'\w+|[^\w\s]', text)

def parse_xml_to_tokens_and_labels(gold_corpus):
    """
    Parses XML content to extract raw text and identify error tokens.
    Returns:
        raw_text (str): The text without tags.
        tokens (list): List of tokens from the raw text.
        labels (list): List of booleans (True if token is part of an error).
    """
    # Handle multiple XML documents in one file by wrapping them in a root tag
    # and removing XML declarations
    gold_corpus = re.sub(r'<\?xml.*?\?>', '', gold_corpus)
    root = ET.fromstring(f"<root>{gold_corpus}</root>")
    
    tokens = []
    labels = []
    raw_text = ""
    last_end = 0

    # Iterate over all elements to find Tokens
    for elem in root.iter():
        # Check if the tag ends with 'Token' (ignoring the long namespace prefix)
        if elem.tag.endswith('Token'):
            begin = int(elem.attrib.get('begin', 0))
            end = int(elem.attrib.get('end', 0))
            text = "".join(elem.itertext())

            # Reconstruct text with original spacing
            if begin > last_end:
                raw_text += " " * (begin - last_end)
            raw_text += text
            last_end = end

            # Check if this token has an error annotation inside it
            is_error = False
            for child in elem.iter():
                if "Errors" in child.tag:
                    is_error = True
                    break
            
            part_tokens = tokenize(text)
            tokens.extend(part_tokens)
            labels.extend([is_error] * len(part_tokens))

    return raw_text, tokens, labels

def correct_text_with_model(text, corrector):
    # Divide into lines
    lines = text.split('\n')

    # Correct each line
    corrected_lines = []
    for line in lines:
        if not line.strip():
            corrected_lines.append(line)
            continue
        try:
            result = corrector(line)
            corrected_lines.append(result[0]['generated_text'])
        except Exception:
            corrected_lines.append(line)
    return "\n".join(corrected_lines)

def get_model_detection_labels(original_tokens, corrected_text):
    corrected_tokens = tokenize(corrected_text)
    matcher = difflib.SequenceMatcher(None, original_tokens, corrected_tokens)
    model_labels = [False] * len(original_tokens)
    
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'replace' or tag == 'delete':
            for k in range(i1, i2):
                model_labels[k] = True
    return model_labels

def compute_metrics(gold_labels, model_labels):
    """ Computes metrics such as Accuracy, Precision, Recall, and F1-score. 
    Also provides the number of True Positives (TP), False Positives (FP), 
    False Negatives (FN), and True Negatives (TN). """

    TP = sum(1 for g, m in zip(gold_labels, model_labels) if g and m)
    FP = sum(1 for g, m in zip(gold_labels, model_labels) if not g and m)
    FN = sum(1 for g, m in zip(gold_labels, model_labels) if g and not m)
    TN = sum(1 for g, m in zip(gold_labels, model_labels) if not g and not m)
    
    total = TP + FP + FN + TN
    return {
        "TP": TP, "FP": FP, "FN": FN, "TN": TN,
        "Accuracy": (TP + TN) / total if total else 0,
        "Precision": TP / (TP + FP) if (TP + FP) else 0,
        "Recall": TP / (TP + FN) if (TP + FN) else 0,
        "F1-score": 2 * TP / (2 * TP + FP + FN) if (2 * TP + FP + FN) else 0
    }

if __name__ == "__main__":
    # Using the codecarbon emissions tracker
    with EmissionsTracker() as tracker:
        corrector, gold_corpus = load_resources()
        raw_text, tokens, gold_labels = parse_xml_to_tokens_and_labels(gold_corpus)
        corrected_text = correct_text_with_model(raw_text, corrector)
        model_labels = get_model_detection_labels(tokens, corrected_text)
        metrics = compute_metrics(gold_labels, model_labels)

        # Print output table with results
        table = PrettyTable(["Metric", "Value"])
        for k, v in metrics.items():
            table.add_row([k, f"{v:.4f}" if isinstance(v, float) else v])
        print(table)
