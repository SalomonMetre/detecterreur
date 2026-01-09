import json
import sys
from pathlib import Path
from collections import defaultdict
from detecterreur.orchestrator import Orchestrator

def calculate_metrics(tp, fp, fn, tn):
    accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    return accuracy, precision, recall, f1

def format_table(stats_dict, title):
    header = f"| {'Type':<20} | {'Acc':<6} | {'Prec':<6} | {'Rec':<6} | {'F1':<6} |"
    sep = "|" + "-"*22 + "|" + "-"*8 + "|" + "-"*8 + "|" + "-"*8 + "|" + "-"*8 + "|"
    rows = [title, sep, header, sep]
    
    # Calculate per-type metrics
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
        rows.append(f"| {label:<20} | {acc:<6.3f} | {p:<6.3f} | {r:<6.3f} | {f1:<6.3f} |")
    
    # Calculate Overall (Micro-average)
    rows.append(sep)
    o_acc, o_p, o_r, o_f1 = calculate_metrics(all_tp, all_fp, all_fn, all_tn)
    rows.append(f"| {'OVERALL':<20} | {o_acc:<6.3f} | {o_p:<6.3f} | {o_r:<6.3f} | {o_f1:<6.3f} |")
    
    return "\n".join(rows)

def main(json_path):
    orc = Orchestrator()
    
    with open(json_path, 'r', encoding='utf-8') as f:
        reference_data = json.load(f)

    # Stats containers: { label: {tp: 0, fp: 0, ...} }
    macro_stats = defaultdict(lambda: {'tp': 0, 'fp': 0, 'fn': 0, 'tn': 0})
    cat_stats = defaultdict(lambda: {'tp': 0, 'fp': 0, 'fn': 0, 'tn': 0})

    # Identify all unique labels across the whole dataset (Ref + Detection)
    # This ensures we account for types that the orchestrator might find but aren't in JSON
    all_macros = set()
    all_cats = set()
    
    # Pre-scan to get the universe of labels
    processed_pairs = []
    print("Running Orchestrator on sentences...")
    for entry in reference_data:
        sentence = entry['sentence']
        ref_macros = set(entry['macro_categories'])
        ref_cats = set(entry['categories'])
        
        # Get Orchestrator results
        results = orc.get_error(sentence)
        det_macros = {cat for cat, name, is_err in results if is_err}
        det_cats = {name for cat, name, is_err in results if is_err}
        
        all_macros.update(ref_macros | det_macros)
        all_cats.update(ref_cats | det_cats)
        processed_pairs.append((ref_macros, det_macros, ref_cats, det_cats))

    # Calculate TP, FP, FN, TN
    for ref_m, det_m, ref_c, det_c in processed_pairs:
        # Macro Layer
        for m in all_macros:
            if m in det_m and m in ref_m: macro_stats[m]['tp'] += 1
            elif m in det_m and m not in ref_m: macro_stats[m]['fp'] += 1
            elif m not in det_m and m in ref_m: macro_stats[m]['fn'] += 1
            else: macro_stats[m]['tn'] += 1
            
        # Category Layer
        for c in all_cats:
            if c in det_c and c in ref_c: cat_stats[c]['tp'] += 1
            elif c in det_c and c not in ref_c: cat_stats[c]['fp'] += 1
            elif c not in det_c and c in ref_c: cat_stats[c]['fn'] += 1
            else: cat_stats[c]['tn'] += 1

    # Generate Reports
    macro_report = format_table(macro_stats, "MACRO-CATEGORY ACCURACY REPORT")
    cat_report = format_table(cat_stats, "CATEGORY ACCURACY REPORT")

    # Save to files
    with open("report_macrocategories.txt", "w", encoding="utf-8") as f:
        f.write(macro_report)
    with open("report_categories.txt", "w", encoding="utf-8") as f:
        f.write(cat_report)

    print("\nEvaluation Complete.")
    print("Saved: report_macrocategories.txt")
    print("Saved: report_categories.txt")

if __name__ == "__main__":
    json_input = "./final_merged_errors.json" if len(sys.argv) < 2 else sys.argv[1]
    main(json_input)