import json
from prettytable import PrettyTable
from concurrent.futures import ProcessPoolExecutor, as_completed
from functools import partial
from codecarbon import track_emissions

# Import all detectors
from detecterreur.forme.form_case import FormCase
from detecterreur.forme.form_diacritic import FormDiacritic
from detecterreur.ortographe.letter_insertion import LetterInsertion
from detecterreur.ortographe.letter_missing import LetterMissing
from detecterreur.ortographe.letter_substitution import LetterSubstitution
from detecterreur.ortographe.letter_order import LetterOrder
from detecterreur.ponctuation.PONC import Punctuation
from detecterreur.grammaire.grammar_conjugation import GrammarConjugation
from detecterreur.grammaire.grammar_euphonic import GrammarEuphonic
from detecterreur.grammaire.grammar_agreement import GrammarAgreement


# ------------- WORKER FUNCTION (RUNS IN PARALLEL) ---------------- #

def evaluate_single_sentence(entry, detector_classes, all_error_types):
    """Run all detectors on a single sentence and return per-sentence TP/FP/FN/TN."""
    text = entry["text"]
    gold_errors = set(entry["errors"].keys())

    detectors = [cls() for cls in detector_classes]

    detected_errors = set()
    for det in detectors:
        has_err, err_type = det.get_error(text)
        if has_err and err_type:
            detected_errors.add(err_type)

    sent_metrics = {et: {"TP": 0, "FP": 0, "FN": 0, "TN": 0} for et in all_error_types}

    for et in all_error_types:
        if et in gold_errors and et in detected_errors:
            sent_metrics[et]["TP"] += 1
        elif et not in gold_errors and et in detected_errors:
            sent_metrics[et]["FP"] += 1
        elif et in gold_errors and et not in detected_errors:
            sent_metrics[et]["FN"] += 1
        else:
            sent_metrics[et]["TN"] += 1

    return sent_metrics


# ---------------- MAIN EVALUATION FUNCTION ---------------- #

@track_emissions
def evaluate_detectors(filepaths=None) -> None:
    """
    Evaluate detectors across one or multiple JSON files.
    filepaths can be:
        - None → default file
        - a single string → one file
        - a list of strings → multiple files
    """

    detector_classes = [
        FormCase,
        FormDiacritic,
        LetterInsertion,
        LetterMissing,
        LetterSubstitution,
        LetterOrder,
        Punctuation,
        GrammarConjugation,
        GrammarEuphonic,
        GrammarAgreement,
    ]

    # ---------- Handle file list ----------
    if filepaths is None:
        filepaths = [
            "testing/final/parsed_output_russo.json",
            "testing/final/parsed_output_sino.json",
            ]
    elif isinstance(filepaths, str):
        filepaths = [filepaths]

    # ---------- Load and merge all gold data ----------
    gold_data = []
    for fp in filepaths:
        with open(fp, "r", encoding="utf-8") as f:
            gold_data.extend(json.load(f))

    total_sentences = len(gold_data)

    # Build known error types
    all_error_types = [cls().error_name for cls in detector_classes]

    metrics = {et: {"TP": 0, "FP": 0, "FN": 0, "TN": 0} for et in all_error_types}

    worker = partial(
        evaluate_single_sentence,
        detector_classes=detector_classes,
        all_error_types=all_error_types,
    )

    # ---------------- PARALLEL EXECUTION ---------------- #

    with ProcessPoolExecutor() as executor:
        futures = [executor.submit(worker, entry) for entry in gold_data]

        for fut in as_completed(futures):
            sent_result = fut.result()
            for et in all_error_types:
                for k in ["TP", "FP", "FN", "TN"]:
                    metrics[et][k] += sent_result[et][k]

    # ---------------- BUILD RESULTS TABLE ---------------- #

    table = PrettyTable()
    table.field_names = [
        "Error Type", "TP", "FP", "FN", "TN",
        "Accuracy", "Precision", "Recall", "F1-score"
    ]

    for et in all_error_types:
        TP = metrics[et]["TP"]
        FP = metrics[et]["FP"]
        FN = metrics[et]["FN"]
        TN = metrics[et]["TN"]

        accuracy = (TP + TN) / total_sentences if total_sentences else 0
        precision = TP / (TP + FP) if (TP + FP) else 0
        recall = TP / (TP + FN) if (TP + FN) else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0

        table.add_row([
            et, TP, FP, FN, TN,
            f"{accuracy:.2%}",
            f"{precision:.2%}",
            f"{recall:.2%}",
            f"{f1:.2%}"
        ])

    total_TP = sum(metrics[et]["TP"] for et in all_error_types)
    total_FP = sum(metrics[et]["FP"] for et in all_error_types)
    total_FN = sum(metrics[et]["FN"] for et in all_error_types)
    total_TN = sum(metrics[et]["TN"] for et in all_error_types)

    overall_accuracy = (total_TP + total_TN) / (total_TP + total_FP + total_FN + total_TN)
    overall_precision = total_TP / (total_TP + total_FP) if (total_TP + total_FP) else 0
    overall_recall = total_TP / (total_TP + total_FN) if (total_TP + total_FN) else 0
    overall_f1 = 2 * overall_precision * overall_recall / (overall_precision + overall_recall) if (overall_precision + overall_recall) else 0

    table.add_row([
        "Overall",
        total_TP,
        total_FP,
        total_FN,
        total_TN,
        f"{overall_accuracy:.2%}",
        f"{overall_precision:.2%}",
        f"{overall_recall:.2%}",
        f"{overall_f1:.2%}"
    ])

    print(f"Files evaluated: {filepaths}")
    print(f"Total sentences tested: {total_sentences}\n")
    print(table)


if __name__ == "__main__":
    evaluate_detectors()
