from pathlib import Path
from Bio.PDB.MMCIF2Dict import MMCIF2Dict
import xml.etree.ElementTree as ET
import argparse
import requests
import gzip

def to_canonical_pdb_id(raw_id: str):
    """
    Converts any supported input into canonical 4-character PDB ID.
    """

    raw_id = raw_id.strip().lower()

    # Extended ID handling
    if raw_id.startswith("pdb_"):
        # best-effort extraction
        return raw_id.split("_")[-1][-4:]

    # Already canonical
    return raw_id

def download_mmcif(pdb_id, outdir):
    url = f"https://files.rcsb.org/download/{pdb_id}.cif"

    r = requests.get(url, timeout=30)

    if r.status_code != 200:
        raise ValueError(f"mmCIF not found for {pdb_id}")

    path = Path(outdir) / f"{pdb_id}.cif"
    path.write_bytes(r.content)

    return path


def download_validation_xml(pdb_id, outdir):
    url = (
        f"https://files.rcsb.org/pub/pdb/validation_reports/"
        f"{pdb_id[1:3]}/{pdb_id}/{pdb_id}_validation.xml.gz"
    )

    r = requests.get(url, timeout=30)

    if r.status_code != 200:
        return None

    gz_path = Path(outdir) / f"{pdb_id}.xml.gz"
    xml_path = Path(outdir) / f"{pdb_id}.xml"

    gz_path.write_bytes(r.content)

    try:
        with gzip.open(gz_path, "rb") as f:
            xml_path.write_bytes(f.read())
    except Exception:
        return None

    return xml_path

def parse_metadata(cif_file):
    d = MMCIF2Dict(str(cif_file))

    def g(k):
        v = d.get(k)
        return v[0] if isinstance(v, list) else v

    return {
        "title": g("_struct.title"),
        "method": g("_exptl.method"),
        "resolution": g("_refine.ls_d_res_high"),
        "deposition_date": g("_pdbx_database_status.recvd_initial_deposition_date"),
    }

import xml.etree.ElementTree as ET

def parse_validation(xml_file):
    if xml_file is None:
        return {}

    tree = ET.parse(xml_file)
    root = tree.getroot()
    entry = root.find("Entry")

    if entry is None:
        return {}

    return {
        "clashscore": entry.attrib.get("clashscore"),
        "rama_outliers": entry.attrib.get("percent-rama-outliers"),
        "rotamer_outliers": entry.attrib.get("percent-rota-outliers"),
        "molprobity": entry.attrib.get("molprobity-score"),
    }

def print_row(data):
    print("\n=== PDB SUMMARY ===\n")
    for k, v in data.items():
        print(f"{k:20}: {v}")

def main():

    parser = argparse.ArgumentParser(
        description="Bulletproof PDB Validation CLI Tool"
    )

    parser.add_argument("pdb_ids", nargs="+")
    parser.add_argument("--out", default="pdb_data")

    args = parser.parse_args()

    results = []

    for raw_id in args.pdb_ids:

        try:
            # STEP 1: normalize ID (CRITICAL)
            pdb_id = to_canonical_pdb_id(raw_id)

            # STEP 2: download data
            cif_file = download_mmcif(pdb_id, args.out)
            xml_file = download_validation_xml(pdb_id, args.out)

            # STEP 3: parse
            meta = parse_metadata(cif_file)
            val = parse_validation(xml_file)

            # STEP 4: merge
            result = {
                "pdb_id": pdb_id.upper(),
                **meta,
                **val
            }

            results.append(result)

            print_row(result)

        except Exception as e:
            print(f"[ERROR] {raw_id}: {e}")


if __name__ == "__main__":
    main()
