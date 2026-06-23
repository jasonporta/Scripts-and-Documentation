#!/usr/bin/env python3

import requests
import pandas as pd

SEARCH_URL = "https://search.rcsb.org/rcsbsearch/v2/query"
ENTRY_URL = "https://data.rcsb.org/rest/v1/core/entry"

authors = ["Porta, J.", "Porta, J.C."]

all_ids = set()

for author in authors:

    query = {
        "query": {
            "type": "terminal",
            "service": "text",
            "parameters": {
                "attribute": "rcsb_primary_citation.rcsb_authors",
                "operator": "contains_phrase",
                "value": author
            }
        },
        "return_type": "entry",
        "request_options": {
            "return_all_hits": True
        }
    }

    r = requests.post(SEARCH_URL, json=query)
    r.raise_for_status()

    results = r.json().get("result_set", [])

    for hit in results:
        all_ids.add(hit["identifier"])

records = []

for pdb_id in sorted(all_ids):

    r = requests.get(f"{ENTRY_URL}/{pdb_id}")
    r.raise_for_status()

    data = r.json()

    title = (
        data.get("struct", {})
            .get("title", "")
    )

    method = (
        data.get("exptl", [{}])[0]
            .get("method", "")
    )

    deposition_date = (
        data.get("rcsb_accession_info", {})
            .get("deposit_date", "")
    )

    resolution = None

    try:
        resolution = data["rcsb_entry_info"]["resolution_combined"][0]
    except Exception:
        pass

    authors = (
        data.get("rcsb_primary_citation", {})
            .get("rcsb_authors", [])
    )

    records.append({
        "PDB_ID": pdb_id,
        "Title": title,
        "Resolution": resolution,
        "Method": method,
        "Deposition_Date": deposition_date,
        "Authors": "; ".join(authors)
    })

df = pd.DataFrame(records)

# Save CSV
df.to_csv("porta_structures.csv", index=False)

# Pretty terminal output
for rec in records:

    print("=" * 80)
    print(f"PDB ID      : {rec['PDB_ID']}")
    print(f"Title       : {rec['Title']}")
    print(f"Resolution  : {rec['Resolution']} Å")
    print(f"Method      : {rec['Method']}")
    print(f"Deposited   : {rec['Deposition_Date']}")
    print(f"Authors     : {rec['Authors']}")
    print()

print("=" * 80)
print(f"Found {len(records)} structures")
print("Saved to porta_structures.csv")
