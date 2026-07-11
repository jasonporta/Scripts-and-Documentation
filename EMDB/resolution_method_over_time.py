#!/usr/bin/env python3

import argparse
import csv
import re
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

"""
Resolution/method trend chart for EMDB depositions.

Plots resolution over time, color-coded by project to plot cryo-EM resolution over career

Usage:
    python resolution_trend.py
    python resolution_trend.py --csv path/to/emdb_depositions_porta.csv --out trend.png

"""

# ---------------------------------------------------------------------------
# Project grouping: edit these keywords to project-names to match your
# own deposition titles.
# ---------------------------------------------------------------------------
PROJECT_RULES = [
    (r"Venezuelan Equine Encephalitis|Chikungunya", "Alphavirus antibody complexes"),
    (r"Zika", "Zika antibody complex"),
    (r"Caveolin", "Caveolin-1 complex"),
    (r"RNA Polymerase|riboswitch", "RNA Pol / riboswitch"),
    (r"Apoferritin", "Apoferritin benchmarks"),
]

PROJECT_COLORS = {
    "Alphavirus antibody complexes": "#1E90FF",
    "Zika antibody complex": "#FF8D1E",
    "Caveolin-1 complex": "#1EFFFE",
    "RNA Pol / riboswitch": "#1E20FF",
    "Apoferritin benchmarks": "#FFFE1E",
    "Other": "#FF1E20",
}

def classify_project(title):
    for pattern, project in PROJECT_RULES:
        if re.search(pattern, title, re.IGNORECASE):
            return project
    return "Other"

def load_depositions(csv_path):
    rows = []
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw_date = (row.get("deposition_date") or "").strip()
            resolution = row.get("resolution", "")
            if not raw_date or not resolution:
                continue
            try:
                date = datetime.fromisoformat(raw_date.replace("Z", "+00:00")).replace(tzinfo=None)
                resolution = float(resolution)
            except ValueError:
                continue
            title = row.get("title", "")
            method = row.get("structure_determination_method", "singleParticle")
            rows.append({
                "emdb_id": row.get("emdb_id", ""),
                "date": date,
                "resolution": resolution,
                "title": title,
                "method": method,
                "project": classify_project(title),
            })
    return sorted(rows, key=lambda r: r["date"])

def build_trend_chart(csv_path, out_path):
    rows = load_depositions(csv_path)
    if not rows:
        print("No depositions with both date and resolution found - nothing to plot.")
        return

    fig, ax = plt.subplots(figsize=(12, 6.5))

    # Plot each project as its own series so the legend groups sensibly.
    projects_seen = []
    for row in rows:
        project = row["project"]
        color = PROJECT_COLORS.get(project, "#999999")
        label = project if project not in projects_seen else None
        if label:
            projects_seen.append(project)
        marker = "o" if row["method"] == "singleParticle" else "^"
        ax.scatter(row["date"], row["resolution"], color=color, s=70,
                  edgecolor="white", linewidth=0.6, zorder=5, label=label, marker=marker)

    # Simple overall trend line (linear fit of resolution vs. time in days)
    if len(rows) >= 2:
        t0 = rows[0]["date"]
        xs = [(r["date"] - t0).days for r in rows]
        ys = [r["resolution"] for r in rows]
        n = len(xs)
        mean_x = sum(xs) / n
        mean_y = sum(ys) / n
        cov = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
        var = sum((x - mean_x) ** 2 for x, y in zip(xs, ys)) or 1
        slope = cov / var
        intercept = mean_y - slope * mean_x
        trend_dates = [rows[0]["date"], rows[-1]["date"]]
        trend_vals = [intercept + slope * x for x in [0, xs[-1]]]
        ax.plot(trend_dates, trend_vals, linestyle="--", color="black",
               alpha=0.5, linewidth=1.2, label="Overall trend", zorder=1)

    # Y-axis: lower Angstrom = better resolution, so put "better" at the top.
    ax.invert_yaxis()
    ax.set_ylabel("Resolution (\u00c5)  \u2014  lower is better")
    ax.set_xlabel("Deposition date")
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    ax.set_title("Resolution Progression Across EMDB Depositions", fontsize=13, weight="bold")
    ax.grid(axis="both", linestyle="--", alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.legend(fontsize=8, loc="lower right", framealpha=0.9)

    # Annotate best and worst resolution points
    best = min(rows, key=lambda r: r["resolution"])
    worst = max(rows, key=lambda r: r["resolution"])
    for r, dy in [(best, 12), (worst, -16)]:
        ax.annotate(f"{r['emdb_id']} ({r['resolution']}\u00c5)",
                   xy=(r["date"], r["resolution"]), xytext=(0, dy),
                   textcoords="offset points", ha="center", fontsize=7.5,
                   arrowprops=dict(arrowstyle="-", color="gray", lw=0.5))

    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    print(f"Saved trend chart to {out_path}")
    print(f"Plotted {len(rows)} depositions with resolution data.")
    print(f"Resolution range: {best['resolution']}\u00c5 (best, {best['emdb_id']}) "
          f"to {worst['resolution']}\u00c5 (worst, {worst['emdb_id']})")

def main():
    parser = argparse.ArgumentParser(description="Generate a resolution/method trend chart from EMDB depositions.")
    parser.add_argument("--csv", default="emdb_depositions_porta.csv",
                        help="Path to EMDB depositions CSV (from list_emdb_depositions.py)")
    parser.add_argument("--out", default="resolution_trend.png", help="Output image path")
    args = parser.parse_args()
    build_trend_chart(args.csv, args.out)

if __name__ == "__main__":
    main()
