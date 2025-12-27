# detecterreur

`detecterreur` is a Python package designed to **detect, correct, and provide educational feedback** on errors made by L2 learners in French written production. It focuses on multiple types of errors, including **orthography, grammar, form, syntax, and punctuation**.

Unlike standard spellcheckers, `detecterreur` distinguishes between **cascaded correction** (pipeline) and **independent suggestions** (atomic error reporting), making it ideal for educational platforms.

---

## Features

The package organizes errors into 5 logical categories:

### 1. **Form-level errors (FORME)**

* **FAGL**: Agglutination
* **FDIA**: Diacritics/Accents
* **FMAJ**: Capitalization

### 2. **Orthography errors (ORTHOGRAPHE)**

* **OINS**: Letter insertion
* **OMIS**: Letter missing
* **OSUB**: Letter substitution
* **OORD**: Letter order

### 3. **Grammar-level errors (GRAMMAIRE)**

* **GCON**: Conjugation
* **GACC**: Agreement
* **GEUF**: Euphony

### 4. **Syntax errors (SYNTAXE)**

* **SORD**: Word order
* **SMIS**: Word missing
* **SINS**: Word insertion
* **SRED**: Redundancy

### 5. **Punctuation (PONCTUATION)**

* **PUNC**: Spacing and missing punctuation

---

## Installation

```bash
pip install git+https://github.com/SalomonMetre/detecterreur
python -m spacy download fr_core_news_sm

```

---

## Quickstart

The core component is the `Orchestrator`, which manages all detection layers.

```python
from detecterreur.orchestrator import Orchestrator

# 1. Initialize
orch = Orchestrator()

text = "..."  # Your input text here

# 2. Get Independent Suggestions
# Returns atomic suggestions per detector. 
# Format: List[Tuple[Category, Name, HasError, SuggestedText]]
suggestions = orch.get_suggestions(text)

for cat, name, has_err, suggestion in suggestions:
    if has_err:
        print(f"[{cat}] {name} detected error. Suggestion: {suggestion}")

# 3. Get Final Cascaded Correction
# Applies all corrections sequentially.
correction = orch.correct(text)
print(f"Final Output: {correction}")

```

---

## How it works

### 1. The Validator (Gatekeeper)

The system uses a **Validator** singleton powered by `spaCy`. Before any orthographic detector processes a word, it queries the Validator to check if the word exists in the French language model. If the word is valid, it is protected from modification.

### 2. Independent vs. Cascaded Logic

* **`get_suggestions()`**: Runs each detector on the **original** input string. This ensures that errors are reported in isolation, preventing the correction of one error from obscuring another in the report.
* **`correct()`**: Runs a **Pipeline**. The output of the Structure layer becomes the input of the Orthography layer, followed by Grammar, Syntax, and Punctuation. This ensures the final output is coherent.

### 3. Specialized Logic

* **Agglutination (FAGL)**: Uses geometric splitting logic based on a strictly defined set of "glue words" (pronouns, determiners) to prevent false positives on compound words.
* **Orthography**: Uses strictly bounded Damerau-Levenshtein distance calculations combined with frequency analysis, applied only to words rejected by the Validator.

---

## License

MIT License © Salomon Metre & Fôtes Fataux Team