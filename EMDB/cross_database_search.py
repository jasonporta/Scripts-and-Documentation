#!/usr/bin/env python3

import argparse
import json
import re
import sys
import urllib.parse
import urllib.request

"""
Cross-database structure search.

Given a UniProt accession (e.g. P0DTC2) or a free-text protein name (e.g.
"caveolin-1"), queries:
  - RCSB PDB Search API   (experimental structures)
  - EMDB Search API       (cryo-EM volumes, by title text match)
  - AlphaFold DB API      (predicted model, UniProt accession only)

Usage:
    python cross_database_search.py P0DTC2
    python cross_database_search.py "caveolin-1"
"""

RCSB_SEARCH_URL = "https://search.rcsb.org/rcsbsearch/v2/query"
EMDB_SEARCH_BASE = "https://www.ebi.ac.uk/emdb/api/search"
ALPHAFOLD_API_BASE = "https://alphafold.ebi.ac.uk/api/prediction"

UNIPROT_PATTERN = re.compile(r"^[OPQ][0-9][A-Z0-9]{3}[0-9]$|^[A-NR-Z][0-9]([A-Z][A-Z0-9]{2}[0-9]){1,2}$")

def fetch_url(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "cross-db-search/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")

def looks_like_uniprot(query):
    return bool(UNIPROT_PATTERN.match(query.upper()))

def search_pdb_by_uniprot(accession):
    payload = {
        "query": {
            "type": "terminal",
            "service": "text",
            "parameters": {
                "attribute": "rcsb_polymer_entity_container_identifiers.reference_sequence_identifiers.database_accession",
                "operator": "exact_match",
                "value": accession,
            },
        },
        "return_type": "entry",
        "request_options": {"paginate": {"start": 0, "rows": 100}},
    }
    return _run_rcsb_query(payload)

def search_pdb_by_text(name):
    payload = {
        "query": {
            "type": "terminal",
            "service": "full_text",
            "parameters": {"value": name},
        },
        "return_type": "entry",
        "request_options": {"paginate": {"start": 0, "rows": 100}},
    }
    return _run_rcsb_query(payload)

def _run_rcsb_query(payload):
    encoded = urllib.parse.quote(json.dumps(payload))
    url = f"{RCSB_SEARCH_URL}?json={encoded}"
    try:
        text = fetch_url(url)
        data = json.loads(text)
    except Exception as e:  # noqa: BLE001
        print(f"  [warning] RCSB query failed: {e}", file=sys.stderr)
        return []
    return [r.get("identifier") for r in data.get("result_set", [])]

def search_emdb_by_text(name):
    # Free-text search of EMDB entry titles for the given protein name
    encoded_query = urllib.parse.quote(f'title:"{name}"')
    fl = urllib.parse.quote("emdb_id,title,resolution,structure_determination_method,fitted_pdbs")
    url = f"{EMDB_SEARCH_BASE}/{encoded_query}?rows=1000&wt=json"
    try:
        text = fetch_url(url)
        data = json.loads(text)
    except Exception as e:  # noqa: BLE001
        print(f"  [warning] EMDB query failed: {e}", file=sys.stderr)
        return []
    # EMDB's JSON response shape wasn't independently confirmed here - try a
    # couple of plausible shapes before giving up.
    docs = data.get("response", {}).get("docs") if isinstance(data, dict) else None
    if docs is None:
        docs = data.get("docs", []) if isinstance(data, dict) else []
    return docs

def fetch_alphafold(accession):
    url = f"{ALPHAFOLD_API_BASE}/{accession}"
    try:
        text = fetch_url(url)
        data = json.loads(text)
        return data
    except Exception as e:  # noqa: BLE001
        print(f"  [warning] AlphaFold DB query failed (API may have changed - see "
              f"https://alphafold.ebi.ac.uk/api-docs): {e}", file=sys.stderr)
        return None

def main():
    parser = argparse.ArgumentParser(description="Search PDB, EMDB, and AlphaFold DB for existing structural data.")
    parser.add_argument("query", help="UniProt accession (e.g. P0DTC2) or protein name (e.g. 'caveolin-1')")
    args = parser.parse_args()

    query = args.query.strip()
    is_uniprot = looks_like_uniprot(query)

    print(f"\nCross-database structure search for: {query}")
    print(f"Interpreted as: {'UniProt accession' if is_uniprot else 'free-text protein name'}\n")

    # --- PDB ---
    print("=== RCSB PDB ===")
    pdb_ids = search_pdb_by_uniprot(query) if is_uniprot else search_pdb_by_text(query)
    if pdb_ids:
        print(f"Found {len(pdb_ids)} PDB entries: {', '.join(pdb_ids[:20])}"
              + (" ..." if len(pdb_ids) > 20 else ""))
    else:
        print("No PDB entries found (or query failed - see warnings above).")

    # --- EMDB ---
    print("\n=== EMDB ===")
    search_term = query if not is_uniprot else query  # EMDB text search only; UniProt not cross-referenced here
    emdb_docs = search_emdb_by_text(search_term)
    if emdb_docs:
        print(f"Found {len(emdb_docs)} EMDB entries (title text match):")
        for doc in emdb_docs[:20]:
            print(f"  {doc.get('emdb_id', '?')}: {doc.get('title', '(no title)')} "
                  f"[{doc.get('resolution', '?')}\u00c5]")
    else:
        print("No EMDB entries found by title text match (or query failed - see warnings above).\n"
              "Note: this is a text match on the title field only, not a true cross-reference,\n"
              "so relevant entries with differently-worded titles may be missed.")

    # --- AlphaFold DB ---
    print("\n=== AlphaFold DB ===")
    if is_uniprot:
        af_data = fetch_alphafold(query)
        if af_data:
            if isinstance(af_data, list) and af_data:
                entry = af_data[0]
            elif isinstance(af_data, dict):
                entry = af_data
            else:
                entry = None
            if entry:
                print(f"Predicted model found: {entry.get('uniprotAccession', query)}")
                print(f"  Model URL: {entry.get('pdbUrl') or entry.get('cifUrl', '(not found in response)')}")
                print(f"  Global confidence (pLDDT summary): "
                      f"{entry.get('globalMetricValue', '(field not found - schema may have changed)')}")
        else:
            print("No AlphaFold prediction found, or the API call failed (see warning above).")
    else:
        print("Skipped - AlphaFold DB is keyed on UniProt accessions, and a free-text name was given.\n"
              "Look up the UniProt accession first (e.g. via https://www.uniprot.org) and re-run with it.")

    print()

if __name__ == "__main__":
    main()
