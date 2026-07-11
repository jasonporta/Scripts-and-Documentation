#!/usr/bin/env python3

import argparse
import csv
import io
import os
import sys
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime
import matplotlib.pyplot as plt

"""
EMDB statistics dashboard.

Pulls field-wide metadata for the entire EMDB archive (subset within a range 
of dates) and generates statistics and charts:
  - Depositions per year
  - Method breakdown (singleParticle, helical, subtomogram averaging, etc.)
  - Resolution distribution and trend over time

Uses the same EMDB search API `fl=` field-list pattern confirmed working in
earlier scripts (list_emdb_depositions.py), extended to a full-archive query.

Usage:
    python emdb_statistics_dashboard.py
    python emdb_statistics_dashboard.py --cache emdb_all.csv   # reuse a saved pull
    python emdb_statistics_dashboard.py --since 2015           # limit by year
"""

BASE = "https://www.ebi.ac.uk/emdb/api"
FIELDS = ["emdb_id", "deposition_date", "structure_determination_method", "resolution"]

def fetch_all_entries(since_year=None):
    # Fetch metadata for every EMDB entry (optionally limited by deposition year)
    if since_year:
        query = f"database:EMDB AND deposition_date:[{since_year}-01-01T00:00:00Z TO *]"
    else:
        query = "database:EMDB AND current_status:[* TO *]"
    encoded_query = urllib.parse.quote(query)
    fl = urllib.parse.quote(",".join(FIELDS))
    url = f"{BASE}/search/{encoded_query}?rows=1000000&wt=csv&download=false&fl={fl}"
    req = urllib.request.Request(url, headers={"User-Agent": "emdb-stats-dashboard/1.0"})
    print(f"Fetching full EMDB metadata (this may take a little while)...", file=sys.stderr)
    with urllib.request.urlopen(req, timeout=180) as resp:
        text = resp.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    return list(reader)

def load_cached(csv_path):
    with open(csv_path, newline="") as f:
        return list(csv.DictReader(f))

def save_cache(rows, csv_path):
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Cached raw data to {csv_path}", file=sys.stderr)

def parse_rows(rows):
    # Convert raw CSV rows into typed records, skipping anything unparseable
    parsed = []
    for row in rows:
        raw_date = (row.get("deposition_date") or "").strip()
        if not raw_date:
            continue
        try:
            date = datetime.fromisoformat(raw_date.replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError:
            continue
        resolution = row.get("resolution", "")
        try:
            resolution = float(resolution) if resolution else None
        except ValueError:
            resolution = None
        method = (row.get("structure_determination_method") or "unknown").strip()
        parsed.append({
            "emdb_id": row.get("emdb_id", ""),
            "date": date,
            "year": date.year,
            "method": method,
            "resolution": resolution,
        })
    return parsed

def plot_depositions_per_year(records, out_path):
    counts = Counter(r["year"] for r in records)
    years = sorted(counts)
    values = [counts[y] for y in years]

    fig, ax = plt.subplots(figsize=(11, 5))
    ax.bar(years, values, color="#1F3864")
    ax.set_xlabel("Year")
    ax.set_ylabel("Depositions")
    ax.set_title("EMDB Depositions per Year", fontsize=13, weight="bold")
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close(fig)
    print(f"Saved {out_path}")

def plot_method_breakdown(records, out_path):
    counts = Counter(r["method"] for r in records)
    # Keep the top N methods, group the rest as "other"
    top_n = 8
    most_common = counts.most_common(top_n)
    other_total = sum(c for _, c in counts.most_common()[top_n:])
    labels = [m for m, _ in most_common]
    values = [c for _, c in most_common]
    if other_total:
        labels.append("other")
        values.append(other_total)

    fig, ax = plt.subplots(figsize=(8, 8))
    colors = plt.cm.Blues_r([i / len(labels) for i in range(len(labels))])
    ax.pie(values, labels=labels, autopct="%1.1f%%", colors=colors, startangle=90,
           textprops={"fontsize": 9})
    ax.set_title("EMDB Structure Determination Method Breakdown", fontsize=13, weight="bold")
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close(fig)
    print(f"Saved {out_path}")

def plot_resolution_trend(records, out_path):
    by_year = defaultdict(list)
    for r in records:
        if r["resolution"] is not None:
            by_year[r["year"]].append(r["resolution"])
    years = sorted(by_year)
    if not years:
        print("No resolution data available to plot.", file=sys.stderr)
        return

    fig, ax = plt.subplots(figsize=(11, 5.5))
    data = [by_year[y] for y in years]
    ax.boxplot(data, positions=years, widths=0.6, showfliers=False,
               patch_artist=True,
               boxprops=dict(facecolor="#4472A8", alpha=0.6),
               medianprops=dict(color="#1F3864", linewidth=1.5))
    ax.invert_yaxis()
    ax.set_xlabel("Year")
    ax.set_ylabel("Resolution (\u00c5) \u2014 lower is better")
    ax.set_title("EMDB Resolution Distribution by Year", fontsize=13, weight="bold")
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    # Thin out x tick labels if there are many years
    step = max(1, len(years) // 15)
    ax.set_xticks(years[::step])
    ax.set_xticklabels([str(y) for y in years[::step]], rotation=45)
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close(fig)
    print(f"Saved {out_path}")

def print_text_summary(records):
    print(f"\nTotal entries analyzed: {len(records)}")
    years = [r["year"] for r in records]
    if years:
        print(f"Year range: {min(years)}\u2013{max(years)}")
    method_counts = Counter(r["method"] for r in records)
    print("\nTop methods:")
    for method, count in method_counts.most_common(10):
        pct = 100 * count / len(records)
        print(f"  {method:<25} {count:>7}  ({pct:5.1f}%)")
    resolutions = [r["resolution"] for r in records if r["resolution"] is not None]
    if resolutions:
        print(f"\nResolution stats (Angstroms): "
              f"best={min(resolutions):.2f}  median={sorted(resolutions)[len(resolutions)//2]:.2f}  "
              f"worst={max(resolutions):.2f}")

def main():
    parser = argparse.ArgumentParser(description="Generate EMDB field-wide statistics and charts.")
    parser.add_argument("--cache", help="Path to a previously-saved raw CSV (skip re-fetching)")
    parser.add_argument("--save-cache", default="emdb_all_entries.csv",
                        help="Where to save the raw pulled data for reuse (default: emdb_all_entries.csv)")
    parser.add_argument("--since", type=int, default=None,
                        help="Only fetch entries deposited since this year (e.g. 2015)")
    parser.add_argument("--outdir", default=".", help="Directory to save output charts")
    args = parser.parse_args()

    if args.cache and os.path.exists(args.cache):
        rows = load_cached(args.cache)
        print(f"Loaded {len(rows)} cached rows from {args.cache}", file=sys.stderr)
    else:
        rows = fetch_all_entries(since_year=args.since)
        save_cache(rows, args.save_cache)

    records = parse_rows(rows)
    print_text_summary(records)

    os.makedirs(args.outdir, exist_ok=True)
    plot_depositions_per_year(records, os.path.join(args.outdir, "emdb_depositions_per_year.png"))
    plot_method_breakdown(records, os.path.join(args.outdir, "emdb_method_breakdown.png"))
    plot_resolution_trend(records, os.path.join(args.outdir, "emdb_resolution_trend.png"))

if __name__ == "__main__":
    main()
