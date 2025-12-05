# detecterreur

`detecterreur` is a Python package designed to **detect, correct, and provide educational feedback** on errors made by L2 learners in French written production. It focuses on multiple types of errors, including **letter, word, grammar, form, syntax, and punctuation** mistakes.

This tool can be integrated into language learning platforms, educational apps, or used for research on French L2 learner errors.

---

## Features

* **Letter-level errors**

  * LINS: Letter insertion
  * LMIS: Letter missing
  * LORD: Letter order
  * LSUB: Letter substitution

* **Word-level errors**

  * SORD: Word order
  * SMIS: Word missing
  * SINS: Word insertion
  * SRED: Word redundancy

* **Form-level errors**

  * FAGL: Form agglutination
  * FDIA: Form diacritics
  * FMAJ: Uppercase/lowercase

* **Grammar-level errors**

  * GCON: Grammar conjugation
  * GEUF: Grammar euphony
  * GACC: Grammar agreement

* **Punctuation errors**

  * PUNC: Detects and corrects punctuation mistakes

---

## Installation

```bash
pip install git+https://github.com/SalomonMetre/detecterreur
```

Or for development / editable install:

```bash
pip install -e .
```

---

## Quickstart

```python
from detecterreur.letter.letter_insertion import LetterInsertion

li = LetterInsertion()

sentence = "Je suis allee a le marchet hier."
has_error = li.has_insertion_error(sentence)
print("Has letter insertion error?", has_error)

corrected = li.correct(sentence)
print("Corrected:", corrected)
```

---

## How it works

* The library uses the **PySpellChecker** for detecting and correcting spelling and letter-level errors.
* It detects errors by comparing words to a French dictionary and uses **Damerau-Levenshtein distance** for fine-grained detection of insertions, deletions, substitutions, and transpositions.
* Sentences are analyzed word-by-word, and corrections preserve punctuation and capitalization where possible.

## Usage

* Detect if a sentence has letter insertion errors:

```python
from detecterreur.letter.letter_insertion import LetterInsertion

li = LetterInsertion()
sentence = "Ceci estt un test."
print(li.has_insertion_error(sentence))  # True
```

* Correct the sentence:

```python
corrected = li.correct(sentence)
print(corrected)  # "Ceci est un test."
```

---

## Educational Feedback

* Each error type can be reported separately, allowing for **tailored feedback** for learners.
* For example, you can highlight letter insertion mistakes (LINS) while leaving other errors untouched, making it easier for learners to focus on one error type at a time.

---

## Contributing

Contributions are welcome! You can:

* Improve French dictionaries
* Add new error detection modules
* Enhance correction algorithms
* Add unit tests and examples

---

## License

MIT License © Salomon Metre & Fôtes Fataux Team
