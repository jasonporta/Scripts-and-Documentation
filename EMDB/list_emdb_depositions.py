#!/usr/bin/env python3

import csv
import io
import sys
import urllib.parse
import urllib.request

"""
Query the EMDB API to list all EMDB deposition for a person(s) by setting 
the AUTHOR_QUERIES variable to their name (last name, first initial).

Uses the EMDB REST API with the `fl` (field list) parameter to write
multiple fields back in one CSV request per author query 
"""

BASE = "https://www.ebi.ac.uk/emdb/api"

# Add name(s) or name variants here if you deposited under other spellings.
AUTHOR_QUERIES = ['author:"Porta J"', 'author:"Porta JC"']

# Fields to request. "title" and "deposition_date" are likely field names
FIELDS = [
    "emdb_id",
    "title",
    "structure_determination_method",
    "resolution",
    "deposition_date",
    "fitted_pdbs",
]

def fetch_url(url):
    req = urllib.request.Request(url, headers={"User-Agent": "emdb-lookup-script/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")

def search_author(author_query):
    # Search EMDB for a given author query, return list of row dicts
    encoded_query = urllib.parse.quote(author_query)
    fl = urllib.parse.quote(",".join(FIELDS))
    url = f"{BASE}/search/{encoded_query}?rows=1000000&wt=csv&download=false&fl={fl}"
    text = fetch_url(url)
    reader = csv.DictReader(io.StringIO(text))
    return list(reader)

def main():
    rows_by_id = {}
    for query in AUTHOR_QUERIES:
        print(f"Searching EMDB for {query} ...", file=sys.stderr)
        try:
            rows = search_author(query)
        except Exception as e:  # noqa: BLE001
            print(f"  [error] request failed: {e}", file=sys.stderr)
            continue
        print(f"  -> found {len(rows)} entries", file=sys.stderr)
        for row in rows:
            emd_id = row.get("emdb_id")
            if emd_id:
                rows_by_id[emd_id] = row

    if not rows_by_id:
        print("No EMDB entries found for the given author names.")
        return

    results = sorted(
        rows_by_id.values(),
        key=lambda r: int(r["emdb_id"].split("-")[1]) if "-" in r.get("emdb_id", "") else 0,
    )

    print(f"\nFound {len(results)} unique EMDB entries:\n")
    print(f"{'EMD ID':<12}{'Method':<18}{'Resolution':<12}{'Deposited':<14}Title")
    print("-" * 110)
    for r in results:
        emd_id = r.get("emdb_id", "")
        method = r.get("structure_determination_method", "") or "-"
        resolution = r.get("resolution", "") or "-"
        deposited_raw = r.get("deposition_date", "") or ""
        deposited = deposited_raw[:10] if deposited_raw else "-"
        title = r.get("title", "") or "(title field blank)"
        print(f"{emd_id:<12}{method:<18}{resolution:<12}{deposited:<14}{title}")

    out_file = "emdb_depositions_porta.csv"
    with open(out_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(results)
    print(f"\nSaved results to {out_file}", file=sys.stderr)

if __name__ == "__main__":
    main()
