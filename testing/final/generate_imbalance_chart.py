import json
import matplotlib.pyplot as plt
from collections import Counter

def plot_error_distribution(filepath: str, output_path="error_distribution.png"):
    # ---- Load the dataset ----
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    # ---- Count error types (once per entry) ----
    counter = Counter()

    for entry in data:
        for err_type in entry["errors"].keys():
            counter[err_type] += 1  # count once per entry

    # ---- Prepare data for chart ----
    labels = list(counter.keys())
    values = list(counter.values())

    # ---- Create pie chart ----
    plt.figure(figsize=(8, 8))
    plt.pie(
        values,
        labels=labels,
        autopct="%1.1f%%",
        startangle=140
    )
    plt.title("Error Type Distribution")
    plt.axis("equal")  # pie should be circular

    # ---- SAVE instead of SHOW ----
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"Saved pie chart to: {output_path}")

# Example usage:
plot_error_distribution("parsed_output_russo.json", "error_distribution_russo.png")
plot_error_distribution("parsed_output_sino.json", "error_distribution_sino.png")