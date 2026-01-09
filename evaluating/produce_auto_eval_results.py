import json
import sys
import re
from pathlib import Path
from collections import defaultdict
from detecterreur.orchestrator import Orchestrator

def calculate_metrics(tp, fp, fn, tn):
    total = tp + tn + fp + fn
    accuracy = (tp + tn) / total if total > 0 else 0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    return accuracy, precision, recall, f1

def format_table(stats_dict, title):
    # Header definition with raw counts and metrics
    header = f"| {'Type':<18} | {'TP':>4} | {'FP':>4} | {'TN':>4} | {'FN':>4} | {'Acc':>6} | {'Prec':>6} | {'Rec':>6} | {'F1':>6} |"
    sep = "|" + "-"*20 + "|" + "-"*6 * 4 + "|" + "-"*8 * 4 + "|"
    
    rows = [f"\n{title}", sep, header, sep]
    
    all_tp, all_fp, all_fn, all_tn = 0, 0, 0, 0
    
    for label in sorted(stats_dict.keys()):
        tp = stats_dict[label]['tp']
        fp = stats_dict[label]['fp']
        fn = stats_dict[label]['fn']
        tn = stats_dict[label]['tn']
        
        all_tp += tp
        all_fp += fp
        all_fn += fn
        all_tn += tn
        
        acc, p, r, f1 = calculate_metrics(tp, fp, fn, tn)
        rows.append(f"| {label:<18} | {tp:>4} | {fp:>4} | {tn:>4} | {fn:>4} | {acc:>6.3f} | {p:>6.3f} | {r:>6.3f} | {f1:>6.3f} |")
    
    # Calculate Overall (Micro-average)
    rows.append(sep)
    o_acc, o_p, o_r, o_f1 = calculate_metrics(all_tp, all_fp, all_fn, all_tn)
    rows.append(f"| {'OVERALL':<18} | {all_tp:>4} | {all_fp:>4} | {all_tn:>4} | {all_fn:>4} | {o_acc:>6.3f} | {o_p:>6.3f} | {o_r:>6.3f} | {o_f1:>6.3f} |")
    
    return "\n".join(rows)

def main(json_path):
    orc = Orchestrator()
    
    if not Path(json_path).exists():
        print(f"Error: {json_path} not found.")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        reference_data = json.load(f)

    macro_stats = defaultdict(lambda: {'tp': 0, 'fp': 0, 'fn': 0, 'tn': 0})
    cat_stats = defaultdict(lambda: {'tp': 0, 'fp': 0, 'fn': 0, 'tn': 0})

    processed_pairs = []
    all_macros = set()
    all_cats = set()

    print(f"Analyzing {len(reference_data)} sentences with Orchestrator...")

    for entry in reference_data:
        sentence = entry['sentence']
        ref_macros = set(entry['macro_categories'])
        ref_cats = set(entry['categories'])
        
        # Run Orchestrator
        results = orc.get_error(sentence)
        
        # Only collect items where is_err is True
        det_macros = {cat.upper() for cat, name, is_err in results if is_err}
        det_cats = {name.upper() for cat, name, is_err in results if is_err}
        
        all_macros.update(ref_macros | det_macros)
        all_cats.update(ref_cats | det_cats)
        processed_pairs.append((ref_macros, det_macros, ref_cats, det_cats))

    # Binary Classification Logic per Label
    for ref_m, det_m, ref_c, det_c in processed_pairs:
        # Evaluate Macros
        for m in all_macros:
            if m in det_m and m in ref_m: macro_stats[m]['tp'] += 1
            elif m in det_m and m not in ref_m: macro_stats[m]['fp'] += 1
            elif m not in det_m and m in ref_m: macro_stats[m]['fn'] += 1
            else: macro_stats[m]['tn'] += 1
            
        # Evaluate Categories
        for c in all_cats:
            if c in det_c and c in ref_c: cat_stats[c]['tp'] += 1
            elif c in det_c and c not in ref_c: cat_stats[c]['fp'] += 1
            elif c not in det_c and c in ref_c: cat_stats[c]['fn'] += 1
            else: cat_stats[c]['tn'] += 1

    # Generate Reports
    macro_table = format_table(macro_stats, "LAYER 1: MACRO-CATEGORY REPORT")
    cat_table = format_table(cat_stats, "LAYER 2: CATEGORY REPORT")

    with open("report_macrocategories.txt", "w", encoding="utf-8") as f:
        f.write(macro_table)
    with open("report_categories.txt", "w", encoding="utf-8") as f:
        f.write(cat_table)

    print("-" * 40)
    print("Reports generated successfully.")
    print(f"Results: {len(all_macros)} macros and {len(all_cats)} categories analyzed.")
    print("-" * 40)

if __name__ == "__main__":
    # Use the filename from previous steps
    main("final_merged_errors.json")