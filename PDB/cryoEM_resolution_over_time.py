import requests
import pandas as pd
import matplotlib.pyplot as plt


# ---------------------------------------------------------
# Query RCSB Search API
# ---------------------------------------------------------

url = "https://search.rcsb.org/rcsbsearch/v2/query"

query = {
    "query": {
        "type": "terminal",
        "service": "text",
        "parameters": {
            "attribute": "exptl.method",
            "operator": "exact_match",
            "value": "ELECTRON MICROSCOPY"
        }
    },
    "return_type": "entry",
    "request_options": {
        "return_all_hits": True
    }
}

response = requests.post(url, json=query)

data = response.json()

pdb_ids = [x["identifier"] for x in data["result_set"]]

print(f"Found {len(pdb_ids)} cryo-EM entries")


# ---------------------------------------------------------
# Fetch metadata from RCSB REST API
# ---------------------------------------------------------

records = []

for pdb_id in pdb_ids:

    api_url = f"https://data.rcsb.org/rest/v1/core/entry/{pdb_id}"

    r = requests.get(api_url)

    if r.status_code != 200:
        continue

    entry = r.json()

    try:
        year = entry[
            "rcsb_accession_info"
        ]["deposit_date"][:4]

        resolution = entry[
            "rcsb_entry_info"
        ]["resolution_combined"][0]

        records.append({
            "pdb_id": pdb_id,
            "year": int(year),
            "resolution": float(resolution)
        })

    except Exception:
        continue


# ---------------------------------------------------------
# Convert to DataFrame
# ---------------------------------------------------------

df = pd.DataFrame(records)

print(df.head())


# ---------------------------------------------------------
# Aggregate by year
# ---------------------------------------------------------

summary = df.groupby("year").agg(
    avg_resolution=("resolution", "mean"),
    best_resolution=("resolution", "min"),
    median_resolution=("resolution", "median"),
    num_structures=("resolution", "count")
).reset_index()


print(summary)


# ---------------------------------------------------------
# Plot trend
# ---------------------------------------------------------

plt.figure(figsize=(10, 6))

plt.plot(
    summary["year"],
    summary["avg_resolution"],
    marker="o",
    label="Average Resolution"
)

plt.plot(
    summary["year"],
    summary["best_resolution"],
    marker="o",
    label="Best Resolution"
)

# Lower resolution numbers are better
plt.gca().invert_yaxis()

plt.xlabel("Year")
plt.ylabel("Resolution (Å)")
plt.title("Improvement in Cryo-EM Resolution Over Time")

plt.legend()

plt.tight_layout()

plt.show()
