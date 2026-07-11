#!/usr/bin/env python3

"""
EMDB deposition completeness checker.

Compares a given EMD ID's metadata (pulled via the EMDB search API) against
a checklist of fields relevant to deposition completeness/quality, based on
wwPDB OneDep's general EM deposition requirements.

  TIER 1 - checked automatically via the API
  TIER 2 - can't be checked this way; script reminds you to check manually
           on the entry's EMDB web page (e.g. https://www.ebi.ac.uk/emdb/EMD-XXXXX)

Usage:
    python deposition_completeness_checker.py EMD-8548
"""

import argparse
import csv
import io
import sys
import urllib.parse
import urllib.request

BASE = "https://www.ebi.ac.uk/emdb/api"

# Fields we can request from the search API for a single entry.
API_FIELDS = [
    "emdb_id",
    "title",
    "structure_determination_method",
    "resolution",
    "deposition_date",
    "fitted_pdbs",
    "average_qscore_value",
    "current_status",
]

# TIER 1: checks we can actually evaluate from the API response.
TIER1_CHECKLIST = [
    ("title", "Title provided"),
    ("structure_determination_method", "Structure determination method recorded"),
    ("resolution", "Reported resolution present"),
    ("deposition_date", "Deposition date present"),
    ("current_status", "Current release status present"),
]

# TIER 2: relevant to real completeness/quality, but not exposed by this
# lightweight search endpoint - included so the checklist is honest about
# what it did and didn't verify. Cross-check these on the entry's web page.
TIER2_MANUAL_CHECKLIST = [
    "Primary citation / publication linked (or explicit 'to be published')",
    "Fitted atomic model (PDB) cross-referenced, if applicable",
    "Half-maps deposited (recommended for FSC validation)",
    "Voxel/pixel spacing and map dimensions recorded",
    "Microscope, voltage, detector, and imaging parameters recorded",
    "Sample/complex composition and source organism recorded",
    "Specimen preparation and vitrification details recorded",
    "Author-recommended contour level provided",
    "Q-score / validation report reviewed and issues addressed",
]

def fetch_entry(emd_id):
    numeric_id = emd_id.upper().replace("EMD-", "").strip()
    query = urllib.parse.quote(f'emdb_id:"EMD-{numeric_id}"')
    fl = urllib.parse.quote(",".join(API_FIELDS))
    url = f"{BASE}/search/{query}?rows=1&wt=csv&download=false&fl={fl}"
    req = urllib.request.Request(url, headers={"User-Agent": "emdb-completeness-checker/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        text = resp.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)
    return rows[0] if rows else None

def print_report(emd_id, entry):
    print(f"\nDeposition completeness check: {emd_id.upper()}\n")

    if entry is None:
        print("No entry found via the search API for this EMD ID. Double-check the ID is correct.")
        return

    print("TIER 1 - automatically checked via EMDB search API:")
    missing = []
    for field, description in TIER1_CHECKLIST:
        value = (entry.get(field) or "").strip()
        status = "[OK]" if value else "[MISSING]"
        display_value = value if value else "(blank)"
        print(f"  {status:<10} {description:<45} value: {display_value}")
        if not value:
            missing.append(description)

    # Q-score and fitted_pdbs are informative but not strictly "required" for
    # a map-only deposition, so reported separately rather than as pass/fail.
    qscore = (entry.get("average_qscore_value") or "").strip()
    fitted = (entry.get("fitted_pdbs") or "").strip()
    print(f"\n  Info: average Q-score value: {qscore or '(not present - map-only entries may not have one)'}")
    print(f"  Info: fitted PDB model(s): {fitted or '(none listed / not exposed by this endpoint)'}")

    print("\nTIER 2 - NOT checkable via this API, verify manually on the entry page:")
    print(f"  https://www.ebi.ac.uk/emdb/{emd_id.upper()}\n")
    for item in TIER2_MANUAL_CHECKLIST:
        print(f"  [ ] {item}")

    print(f"\nSummary: {len(TIER1_CHECKLIST) - len(missing)}/{len(TIER1_CHECKLIST)} "
          f"Tier 1 fields present.", end=" ")
    if missing:
        print(f"Missing: {', '.join(missing)}.")
    else:
        print("All Tier 1 fields present.")

def main():
    parser = argparse.ArgumentParser(description="Check EMDB deposition completeness for an EMD ID.")
    parser.add_argument("emd_id", help='EMD ID, e.g. "EMD-8548" or "8548"')
    args = parser.parse_args()

    try:
        entry = fetch_entry(args.emd_id)
    except Exception as e:  # noqa: BLE001
        print(f"Failed to fetch entry {args.emd_id}: {e}", file=sys.stderr)
        sys.exit(1)

    print_report(args.emd_id, entry)

if __name__ == "__main__":
    main()
