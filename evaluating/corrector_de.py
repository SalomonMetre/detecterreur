import os
import csv
import re
from codecarbon import EmissionsTracker

# Import all detectors
from detecterreur.forme.form_case import FormCase
from detecterreur.forme.form_diacritic import FormDiacritic
from detecterreur.forme.form_agglutination import FormAgglutination
from detecterreur.ortographe.letter_insertion import LetterInsertion
from detecterreur.ortographe.letter_missing import LetterMissing
from detecterreur.ortographe.letter_substitution import LetterSubstitution
from detecterreur.ortographe.letter_order import LetterOrder
from detecterreur.ponctuation.PONC import Punctuation
from detecterreur.grammaire.grammar_conjugation import GrammarConjugation
from detecterreur.grammaire.grammar_euphonic import GrammarEuphonic
from detecterreur.grammaire.grammar_agreement import GrammarAgreement
from detecterreur.syntax.syntax_order import SyntaxOrder
from detecterreur.syntax.syntax_insertion import SyntaxInsertion
from detecterreur.syntax.syntax_missing import SyntaxMissing
from detecterreur.syntax_redundancy import SyntaxRedundancy


def load_resources():
    # Load text to correct
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, 'test_raw.txt')

    with open(file_path, 'r', encoding='utf-8') as f:
        text_to_correct = f.read()

    return text_to_correct

def split_into_sentences(text):
    # Splitting into sentences using regex to include ?, !, and .
    parts = re.split(r'([.?!])', text)
    sentences = []
    for i in range(0, len(parts) - 1, 2):
        if parts[i].strip():
            sentences.append(parts[i].strip() + parts[i+1])
    if len(parts) % 2 != 0 and parts[-1].strip():
        sentences.append(parts[-1].strip())
    return sentences

def process_sentences_with_detecterreur(sentences, detectors):
    """
    Processes sentences with DetectErreur and returns a list of detection result strings.
    """
    results = []
    for sentence in sentences:
        detection_results = []
        for detector in detectors:
            # Must call correct() to analyze the sentence and update internal state
            detector.correct(sentence)
            has_error = detector.get_error()
            detection_results.append(str(has_error))
        
        results.append(", ".join(detection_results))
    return results

def save_to_csv(data, filename="comparison_results.csv"):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, filename)
    
    rows = []
    with open(file_path, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        rows = list(reader)

    col_index = rows[0].index("DetectErreur Correction")

    for i, result in enumerate(data):
        if i + 1 < len(rows):
            rows[i + 1][col_index] = result

    with open(file_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerows(rows)

if __name__ == "__main__":
    # Initialize detectors
    detectors = [
        FormCase(),
        FormDiacritic(),
        FormAgglutination(),
        LetterInsertion(),
        LetterMissing(),
        LetterSubstitution(),
        LetterOrder(),
        SyntaxOrder(),
        SyntaxInsertion(),
        SyntaxMissing(),
        SyntaxRedundancy(),
        Punctuation(),
        GrammarConjugation(),
        GrammarEuphonic(),
        GrammarAgreement()
    ]

    with EmissionsTracker(output_file="emissions.csv") as tracker:
        text_to_correct = load_resources()
        sentences = split_into_sentences(text_to_correct)
        
        print(f"Processing {len(sentences)} sentences with {len(detectors)} detectors...")
        
        results = process_sentences_with_detecterreur(sentences, detectors)
        
        save_to_csv(results)
        
