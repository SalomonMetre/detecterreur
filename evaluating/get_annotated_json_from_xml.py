import json
import re
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
# Add your XML filenames to this list
xml_files = [
    "./9_CHN_L3.xml",
    "./10_PL_M1.xml",
    "./13_PL_L3.xml"
]
output_filename = "final_merged_errors.json"
# ---------------------

def clean_text(text):
    """Removes newlines, tabs, and collapses multiple spaces into one."""
    if not text:
        return ""
    text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    return re.sub(r'\s+', ' ', text).strip()

def process_single_xml(xml_path):
    """Parses a single XML and returns a list of sentence dictionaries."""
    try:
        with open(xml_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'xml')
    except FileNotFoundError:
        print(f"Error: File '{xml_path}' not found. Skipping.")
        return []

    file_results = []
    sentences = soup.find_all('de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Sentence')

    for sentence_tag in sentences:
        tokens = sentence_tag.find_all('de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Token')
        
        raw_text_parts = []
        macro_categories = set()
        categories = set()

        for token in tokens:
            t_text = clean_text(token.get_text())
            if t_text:
                raw_text_parts.append(t_text)

            # Extract Macro-categories (Erros)
            for et in token.find_all('webanno.custom.Errors_Ftes_Fataux'):
                if et.has_attr('Erros'):
                    macro_categories.add(et['Erros'].upper())

            # Extract Sub-categories (ErrorsSubCat)
            for st in token.find_all('webanno.custom.Errors_Ftes_Fataux_Sub_Cat'):
                if st.has_attr('ErrorsSubCat'):
                    categories.add(st['ErrorsSubCat'].upper())

        # Join and fix punctuation/apostrophe spacing
        full_sentence = " ".join(raw_text_parts)
        full_sentence = re.sub(r'\s+([,.!?])', r'\1', full_sentence)
        full_sentence = full_sentence.replace("’ ", "’").replace(" ’", "’")

        file_results.append({
            "sentence": full_sentence,
            "macro_categories": sorted(list(macro_categories)),
            "categories": sorted(list(categories))
        })
    
    return file_results

def main():
    all_data = []
    
    print(f"Starting processing for {len(xml_files)} files...")

    for file_path in xml_files:
        sentences_from_file = process_single_xml(file_path)
        all_data.extend(sentences_from_file)
        print(f" - {file_path}: {len(sentences_from_file)} sentences found.")

    # Final Save
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=4)

    print("-" * 40)
    print(f"SUCCESS!")
    print(f"Total sentences found across all files: {len(all_data)}")
    print(f"Merged JSON saved as: {output_filename}")
    print("-" * 40)

if __name__ == "__main__":
    main()