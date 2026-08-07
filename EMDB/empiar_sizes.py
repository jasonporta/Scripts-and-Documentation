#!/usr/bin/env python3
"""
empiar_sizes.py -- harvest dataset sizes for every EMPIAR entry and report statistics.

EMPIAR (https://www.ebi.ac.uk/empiar/) exposes a public REST API:

    https://www.ebi.ac.uk/empiar/api/entry/all/        -> every entry, one JSON blob
    https://www.ebi.ac.uk/empiar/api/entry/10002/      -> a single entry

Each entry carries a reported total dataset size (the bytes actually sitting on
EMPIAR's FTP server). This script collects that number for all entries, caches
the raw JSON locally so re-runs are free, and prints/writes summary statistics.

Usage
-----
    python empiar_sizes.py                      # fetch everything, print summary
    python empiar_sizes.py --csv sizes.csv      # also write a per-entry CSV
    python empiar_sizes.py --inspect 10002      # dump one entry's JSON keys
    python empiar_sizes.py --per-entry          # slow path: one request per entry
    python empiar_sizes.py --offline            # use only the local cache

Only stdlib is required. `requests` is used if installed, else urllib.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import statistics
import sys
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Iterable

API_ROOT = "https://www.ebi.ac.uk/empiar/api"
ALL_ENTRIES_URL = f"{API_ROOT}/entry/all/"
ENTRY_URL = API_ROOT + "/entry/{eid}/"
CACHE_DIR = Path.home() / ".cache" / "empiar_sizes"
USER_AGENT = "empiar-sizes/1.0 (dataset size survey; contact: you@example.com)"

TB = 1024.0 ** 4
GB = 1024.0 ** 3


# --------------------------------------------------------------------------- #
# HTTP
# --------------------------------------------------------------------------- #
def http_get_json(url: str, timeout: int = 120, retries: int = 4) -> Any:
    """GET a URL and parse JSON, with exponential backoff on transient errors."""
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT,
                                                       "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8", errors="replace"))
        except urllib.error.HTTPError as e:
            # 404 means the accession simply does not exist -- do not retry.
            if e.code == 404:
                return None
            last_err = e
        except Exception as e:  # noqa: BLE001 - network layer is genuinely varied
            last_err = e
        time.sleep(2 ** attempt)
    raise RuntimeError(f"failed to fetch {url}: {last_err}")


# --------------------------------------------------------------------------- #
# Size parsing
# --------------------------------------------------------------------------- #
_UNIT_FACTORS = {
    "b": 1, "byte": 1, "bytes": 1,
    "kb": 1024, "kib": 1024,
    "mb": 1024 ** 2, "mib": 1024 ** 2,
    "gb": 1024 ** 3, "gib": 1024 ** 3,
    "tb": 1024 ** 4, "tib": 1024 ** 4,
    "pb": 1024 ** 5, "pib": 1024 ** 5,
}

# Key names EMPIAR has used / might use for the reported total size.
_SIZE_KEYS = ("dataset_size", "datasetSize", "size", "total_size",
              "entry_size", "dataset_size_bytes")


def parse_size_to_bytes(value: Any) -> int | None:
    """Coerce EMPIAR's size field to bytes.

    Handles raw ints ("1234567"), floats, and unit-suffixed strings
    ("8.5 TB", "500GB", "1,024 MiB"). Returns None if unparseable.
    """
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(value) if value > 0 else None

    text = str(value).strip().replace(",", "")
    if not text:
        return None

    m = re.match(r"^([0-9]*\.?[0-9]+)\s*([a-zA-Z]*)$", text)
    if not m:
        return None
    number = float(m.group(1))
    unit = m.group(2).lower()
    if not unit:  # bare number == bytes
        return int(number) if number > 0 else None
    factor = _UNIT_FACTORS.get(unit)
    if factor is None:
        return None
    return int(number * factor) or None


def extract_size(entry: dict) -> int | None:
    """Find the reported dataset size anywhere in an entry record."""
    for key in _SIZE_KEYS:
        if key in entry:
            size = parse_size_to_bytes(entry[key])
            if size:
                return size
    # Last resort: any top-level key that looks size-ish.
    for key, val in entry.items():
        if "size" in key.lower() and not isinstance(val, (dict, list)):
            size = parse_size_to_bytes(val)
            if size:
                return size
    return None


def extract_year(entry: dict) -> int | None:
    for key in ("release_date", "deposition_date", "public_release_date", "update_date"):
        val = entry.get(key)
        if isinstance(val, str):
            m = re.search(r"(19|20)\d{2}", val)
            if m:
                return int(m.group(0))
    return None


def extract_categories(entry: dict) -> list[str]:
    """Image-set categories, e.g. 'micrographs - multiframe', 'tilt series'."""
    cats: list[str] = []
    for imgset in entry.get("imagesets") or []:
        if not isinstance(imgset, dict):
            continue
        cat = imgset.get("category") or imgset.get("image_category")
        if isinstance(cat, dict):
            cat = cat.get("name") or cat.get("category")
        if isinstance(cat, str) and cat.strip():
            cats.append(cat.strip())
    return cats


# --------------------------------------------------------------------------- #
# Fetching
# --------------------------------------------------------------------------- #
def normalise_accession(key: str) -> str:
    """'EMPIAR-10002' / '10002' / 10002 -> 'EMPIAR-10002'."""
    key = str(key).strip().upper()
    if key.startswith("EMPIAR-"):
        return key
    return f"EMPIAR-{key}"


def fetch_all_entries(cache: Path, offline: bool = False) -> dict[str, dict]:
    """Fetch the bulk /entry/all/ endpoint (one big request)."""
    blob_path = cache / "entry_all.json"
    if blob_path.exists():
        print(f"[cache] reading {blob_path}", file=sys.stderr)
        return json.loads(blob_path.read_text())
    if offline:
        raise SystemExit("--offline set but no cached bulk download exists")

    print(f"[net] GET {ALL_ENTRIES_URL} (this is large, be patient)", file=sys.stderr)
    data = http_get_json(ALL_ENTRIES_URL, timeout=600)
    if data is None:
        raise SystemExit("bulk endpoint returned nothing; retry with --per-entry")
    cache.mkdir(parents=True, exist_ok=True)
    blob_path.write_text(json.dumps(data))
    return data


def fetch_entry(eid: int, cache: Path, offline: bool = False) -> dict | None:
    """Fetch one accession, using an on-disk cache."""
    path = cache / "entries" / f"{eid}.json"
    if path.exists():
        text = path.read_text()
        return json.loads(text) if text.strip() else None
    if offline:
        return None

    data = http_get_json(ENTRY_URL.format(eid=eid))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data) if data is not None else "")
    return data


def fetch_range(start: int, end: int, cache: Path, workers: int,
                offline: bool = False) -> dict[str, dict]:
    """Walk an accession range concurrently. Missing IDs are skipped."""
    found: dict[str, dict] = {}
    ids = range(start, end + 1)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(fetch_entry, eid, cache, offline): eid for eid in ids}
        done = 0
        for fut in as_completed(futures):
            eid = futures[fut]
            done += 1
            if done % 100 == 0:
                print(f"[net] {done}/{len(ids)} accessions probed", file=sys.stderr)
            try:
                data = fut.result()
            except Exception as e:  # noqa: BLE001
                print(f"[warn] {eid}: {e}", file=sys.stderr)
                continue
            if not data:
                continue
            # Response is {"EMPIAR-10002": {...}}; occasionally the bare record.
            if isinstance(data, dict) and len(data) == 1 and \
                    next(iter(data)).upper().startswith("EMPIAR-"):
                acc, record = next(iter(data.items()))
            else:
                acc, record = normalise_accession(eid), data
            if isinstance(record, dict):
                found[normalise_accession(acc)] = record
    return found


# --------------------------------------------------------------------------- #
# Statistics
# --------------------------------------------------------------------------- #
def human(n: float) -> str:
    for unit, factor in (("PB", 1024 ** 5), ("TB", TB), ("GB", GB),
                         ("MB", 1024 ** 2), ("KB", 1024)):
        if n >= factor:
            return f"{n / factor:.2f} {unit}"
    return f"{n:.0f} B"


def summarise(records: list[dict]) -> None:
    sized = [r for r in records if r["size_bytes"]]
    sizes = sorted(r["size_bytes"] for r in sized)

    print("\n" + "=" * 64)
    print("EMPIAR dataset size survey")
    print("=" * 64)
    print(f"entries retrieved      : {len(records)}")
    print(f"entries with a size    : {len(sized)}")
    print(f"entries missing a size : {len(records) - len(sized)}")
    if not sizes:
        print("\nNo sizes parsed -- run with --inspect <id> to see the field names.")
        return

    total = sum(sizes)
    mean = total / len(sizes)
    median = statistics.median(sizes)
    geo = math.exp(sum(math.log(s) for s in sizes) / len(sizes))

    print(f"\ntotal archived         : {human(total)}")
    print(f"mean (arithmetic)      : {human(mean)}")
    print(f"median                 : {human(median)}")
    print(f"geometric mean         : {human(geo)}")
    if len(sizes) > 1:
        print(f"std deviation          : {human(statistics.stdev(sizes))}")
    print(f"min / max              : {human(sizes[0])} / {human(sizes[-1])}")

    print("\npercentiles")
    for p in (5, 25, 50, 75, 90, 95, 99):
        idx = min(len(sizes) - 1, int(round((p / 100) * (len(sizes) - 1))))
        print(f"  p{p:<3} {human(sizes[idx])}")

    print("\ndistribution (log10 buckets)")
    buckets: Counter[int] = Counter(int(math.log10(s)) for s in sizes)
    for exp in sorted(buckets):
        lo, hi = 10 ** exp, 10 ** (exp + 1)
        bar = "#" * max(1, round(40 * buckets[exp] / max(buckets.values())))
        print(f"  {human(lo):>9} - {human(hi):>9} | {buckets[exp]:>5} {bar}")

    by_year: dict[int, list[int]] = defaultdict(list)
    for r in sized:
        if r["year"]:
            by_year[r["year"]].append(r["size_bytes"])
    if by_year:
        print("\nby release year")
        print(f"  {'year':<6}{'n':>6}{'mean':>12}{'median':>12}{'total':>12}")
        for year in sorted(by_year):
            vals = by_year[year]
            print(f"  {year:<6}{len(vals):>6}"
                  f"{human(sum(vals) / len(vals)):>12}"
                  f"{human(statistics.median(vals)):>12}"
                  f"{human(sum(vals)):>12}")

    print("\nlargest 10 entries")
    for r in sorted(sized, key=lambda r: -r["size_bytes"])[:10]:
        print(f"  {r['accession']:<15}{human(r['size_bytes']):>10}  {r['title'][:60]}")
    print()


def write_csv(records: list[dict], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["accession", "size_bytes", "size_tb",
                                                "year", "categories", "title"])
        writer.writeheader()
        for r in sorted(records, key=lambda r: r["accession"]):
            writer.writerow({
                "accession": r["accession"],
                "size_bytes": r["size_bytes"] or "",
                "size_tb": f"{r['size_bytes'] / TB:.6f}" if r["size_bytes"] else "",
                "year": r["year"] or "",
                "categories": "; ".join(sorted(set(r["categories"]))),
                "title": r["title"],
            })
    print(f"[out] wrote {path}", file=sys.stderr)


# --------------------------------------------------------------------------- #
# Assembly
# --------------------------------------------------------------------------- #
def build_records(entries: dict[str, dict]) -> list[dict]:
    records = []
    for acc, entry in entries.items():
        if not isinstance(entry, dict):
            continue
        records.append({
            "accession": normalise_accession(acc),
            "size_bytes": extract_size(entry),
            "year": extract_year(entry),
            "categories": extract_categories(entry),
            "title": (entry.get("title") or "").strip().replace("\n", " "),
        })
    return records


def main(argv: Iterable[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", type=Path, help="write per-entry results to this CSV")
    ap.add_argument("--json", type=Path, help="write per-entry results to this JSON")
    ap.add_argument("--cache", type=Path, default=CACHE_DIR,
                    help=f"cache directory (default: {CACHE_DIR})")
    ap.add_argument("--per-entry", action="store_true",
                    help="probe accessions one by one instead of the bulk endpoint")
    ap.add_argument("--start", type=int, default=10001, help="first accession number")
    ap.add_argument("--end", type=int, default=13500, help="last accession number")
    ap.add_argument("--workers", type=int, default=8, help="concurrent requests")
    ap.add_argument("--offline", action="store_true", help="use cached data only")
    ap.add_argument("--inspect", type=str,
                    help="print the raw JSON for one accession and exit")
    args = ap.parse_args(list(argv) if argv is not None else None)

    if args.inspect:
        eid = re.sub(r"\D", "", args.inspect)
        data = fetch_entry(int(eid), args.cache, args.offline)
        print(json.dumps(data, indent=2)[:8000])
        if isinstance(data, dict) and len(data) == 1:
            record = next(iter(data.values()))
            if isinstance(record, dict):
                print("\ntop-level keys:", ", ".join(sorted(record)), file=sys.stderr)
                print("parsed size   :", extract_size(record), file=sys.stderr)
        return 0

    if args.per_entry:
        entries = fetch_range(args.start, args.end, args.cache, args.workers,
                              args.offline)
    else:
        entries = fetch_all_entries(args.cache, args.offline)

    records = build_records(entries)
    if not records:
        print("no entries retrieved", file=sys.stderr)
        return 1

    summarise(records)
    if args.csv:
        write_csv(records, args.csv)
    if args.json:
        args.json.write_text(json.dumps(records, indent=2))
        print(f"[out] wrote {args.json}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
