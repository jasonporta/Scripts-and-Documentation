import requests

YEAR = 2002

search_url = "https://search.rcsb.org/rcsbsearch/v2/query"

query = {
    "query": {
        "type": "group",
        "logical_operator": "and",
        "nodes": [
            {
                "type": "terminal",
                "service": "text",
                "parameters": {
                    "attribute": "rcsb_accession_info.deposit_date",
                    "operator": "greater_or_equal",
                    "value": f"{YEAR}-01-01"
                }
            },
            {
                "type": "terminal",
                "service": "text",
                "parameters": {
                    "attribute": "rcsb_accession_info.deposit_date",
                    "operator": "less_or_equal",
                    "value": f"{YEAR}-12-31"
                }
            },
            {
                "type": "terminal",
                "service": "text",
                "parameters": {
                    "attribute": "exptl.method",
                    "operator": "exact_match",
                    "value": "ELECTRON MICROSCOPY"
                }
            }
        ]
    },
    "return_type": "entry",
    "request_options": {
        "return_all_hits": True
    }
}

response = requests.post(search_url, json=query)

# Debugging output
print("Status code:", response.status_code)
print(response.text[:500])

data = response.json()

if "result_set" not in data:
    raise RuntimeError("Search failed:\n" + str(data))

results = data["result_set"]

pdb_ids = [r["identifier"] for r in results]

print(f"\nFound {len(pdb_ids)} cryo-EM entries deposited in {YEAR}\n")

# Retrieve resolutions
for pdb_id in pdb_ids:

    url = f"https://data.rcsb.org/rest/v1/core/entry/{pdb_id}"

    r = requests.get(url)

    if r.status_code != 200:
        continue

    entry = r.json()

    try:
        resolution = entry["rcsb_entry_info"]["resolution_combined"][0]
    except:
        resolution = "N/A"

    print(f"{pdb_id}\t{resolution} Å")
