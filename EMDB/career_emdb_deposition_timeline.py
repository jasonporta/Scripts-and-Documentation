#!/usr/bin/env python3

import argparse
import csv
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Patch

"""
Career timeline generator.

Combines employment/education history with EMDB deposition dates into a single visual timeline

Usage:
    python career_timeline.py
    python career_timeline.py --csv path/to/emdb_depositions_porta.csv --out timeline.png

"""

# ---------------------------------------------------------------------------
# Employment / education history - edit this list to update your timeline.
# Each entry: (label, organization, start_date, end_date, category)
# category is used only to color-code the bars.
# ---------------------------------------------------------------------------
EMPLOYMENT = [
    ("Research Technician", "UNMC (Borgstahl Lab)", "2004-01-01", "2006-12-31", "technician"),
    ("PhD, Structural Biology", "UNMC (Borgstahl Lab)", "2007-01-01", "2011-12-31", "training"),
    ("Postdoctoral Researcher", "Purdue University (Rossmann Lab)", "2012-04-01", "2017-03-31", "postdoc"),
    ("Postdoctoral Researcher", "University of Michigan (Ohi Lab)", "2017-09-01", "2023-08-31", "postdoc"),
    ("Staff Scientist", "Hormel Institute, University of Minnesota", "2024-05-01", "2025-06-30", "staff"),
]

CATEGORY_COLORS = {
    "technician":   "#1E20FF",    
    "training":     "#1E90FF",
    "postdoc":      "#FF8D1E",
    "staff":        "#1EFFFE",
}

def load_depositions(csv_path):
    """Read EMDB deposition CSV (from list_emdb_depositions.py) and return
    a list of (emdb_id, date, resolution, title) tuples."""
    depositions = []
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw_date = (row.get("deposition_date") or "").strip()
            if not raw_date:
                continue
            try:
                date = datetime.fromisoformat(raw_date.replace("Z", "+00:00")).replace(tzinfo=None)
            except ValueError:
                continue
            resolution = row.get("resolution", "")
            try:
                resolution = float(resolution)
            except (TypeError, ValueError):
                resolution = None
            depositions.append((row.get("emdb_id", ""), date, resolution, row.get("title", "")))
    return sorted(depositions, key=lambda d: d[1])

def build_timeline(csv_path, out_path):
    depositions = load_depositions(csv_path)

    fig, ax = plt.subplots(figsize=(14, 7))

    # Employment bars
    y_emp = 1
    seen_categories = set()
    for label, org, start, end, category in EMPLOYMENT:
        start_dt = datetime.fromisoformat(start)
        end_dt = datetime.fromisoformat(end)
        width_days = (end_dt - start_dt).days
        ax.barh(
            y_emp, width_days, left=start_dt, height=0.6,
            color=CATEGORY_COLORS.get(category, "#999999"),
            edgecolor="white", label=category if category not in seen_categories else None,
        )
        seen_categories.add(category)
        mid = start_dt + (end_dt - start_dt) / 2
        text = f"{label}\n{org}"
        # Short bars (e.g. Hormel's ~14 months) can't fit the label inside -
        # place those labels above the bar instead, pointing down to it.
        if width_days < 550:  # roughly ~18 months
            ax.annotate(
                text, xy=(mid, y_emp + 0.32), xytext=(mid, y_emp + 0.85),
                ha="center", va="bottom", fontsize=7.5, weight="bold", color="#1F3864",
                arrowprops=dict(arrowstyle="-", color="#1F3864", lw=0.8),
            )
        else:
            ax.text(mid, y_emp, text, ha="center", va="center",
                    fontsize=7.5, color="white", weight="bold")
        y_emp += 1

    # Deposition markers: jitter vertically when dates cluster together
    y_dep_base = -0.4
    dep_dates = [d[1] for d in depositions]
    dep_res = [d[2] if d[2] is not None else 10 for d in depositions]

    # Group depositions that fall within CLUSTER_WINDOW days of each other and
    # stack them vertically so overlapping markers become readable.
    CLUSTER_WINDOW_DAYS = 10
    ROW_STEP = 0.35
    y_positions = []
    cluster_start_idx = 0
    for i in range(len(depositions)):
        if i == 0:
            y_positions.append(0)
            continue
        gap = (depositions[i][1] - depositions[cluster_start_idx][1]).days
        if gap > CLUSTER_WINDOW_DAYS:
            cluster_start_idx = i
            y_positions.append(0)
        else:
            # how many points already placed in this cluster
            count_in_cluster = sum(1 for j in range(cluster_start_idx, i))
            y_positions.append(count_in_cluster)

    y_scatter = [y_dep_base - (pos * ROW_STEP) for pos in y_positions]

    if dep_dates:
        sizes = [max(25, 400 / r) for r in dep_res]  # smaller resolution -> bigger marker
        ax.scatter(dep_dates, y_scatter, s=sizes, color="#C0392B",
                   alpha=0.75, zorder=5, edgecolor="white", linewidth=0.5,
                   label="EMDB deposition")

        # Annotate first, last, and best-resolution entries only, to avoid clutter
        notable_idx = {0, len(depositions) - 1}
        best_res_idx = min(range(len(depositions)),
                            key=lambda i: depositions[i][2] if depositions[i][2] else 999)
        notable_idx.add(best_res_idx)
        for i in sorted(notable_idx):
            emd_id, date, res, title = depositions[i]
            ax.annotate(
                f"{emd_id} ({res}\u00c5)" if res else emd_id,
                xy=(date, y_scatter[i]), xytext=(0, -14 - (y_positions[i] * 5)),
                textcoords="offset points",
                ha="center", fontsize=7,
                arrowprops=dict(arrowstyle="-", color="gray", lw=0.5),
            )

    # Formatting
    ax.set_yticks([])
    min_y = min(y_scatter) - 0.6 if dep_dates else -1
    ax.set_ylim(min_y, len(EMPLOYMENT) + 2)
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.set_xlabel("Year")
    ax.set_title("Jason Porta, PhD — Career Timeline & EMDB Depositions (22 entries)",
                 fontsize=13, weight="bold")

    legend_elements = [
        Patch(facecolor=CATEGORY_COLORS["technician"], label="Research Technician"),
        Patch(facecolor=CATEGORY_COLORS["training"], label="Training/PhD"),
        Patch(facecolor=CATEGORY_COLORS["postdoc"], label="Postdoctoral research"),
        Patch(facecolor=CATEGORY_COLORS["staff"], label="Staff scientist"),
        plt.Line2D([0], [0], marker="o", color="w", markerfacecolor="#C0392B",
                   markersize=8, label="EMDB deposition (size = resolution)"),
    ]
    ax.legend(handles=legend_elements, loc="upper left", fontsize=8, framealpha=0.9)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.grid(axis="x", linestyle="--", alpha=0.3)

    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    print(f"Saved timeline to {out_path}")
    print(f"Plotted {len(depositions)} EMDB depositions and {len(EMPLOYMENT)} employment periods.")

def main():
    parser = argparse.ArgumentParser(description="Generate a career timeline with EMDB depositions.")
    parser.add_argument("--csv", default="emdb_depositions_porta.csv",
                        help="Path to EMDB depositions CSV (from list_emdb_depositions.py)")
    parser.add_argument("--out", default="career_timeline.png", help="Output image path")
    args = parser.parse_args()
    build_timeline(args.csv, args.out)

if __name__ == "__main__":
    main()
