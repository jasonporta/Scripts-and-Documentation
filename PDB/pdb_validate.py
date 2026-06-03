import argparse
import csv
import gzip
import requests
from pathlib import Path
from Bio.PDB import PDBList
from Bio.PDB.MMCIF2Dict import MMCIF2Dict
import xml.etree.ElementTree as ET

# Download mmCIF
def download_mmcif(pdb_id, outdir):
    pdb_id = pdb_id.lower().strip()

    pdbl = PDBList()
    filename = pdbl.retrieve_pdb_file(
        pdb_id,
        pdir=str(outdir),
        file_format="mmCif",
        overwrite=True
    )
    return filename


# Download validation XML
def download_validation_xml(pdb_id, outdir):
    pdb_id = pdb_id.lower().strip()
    middle = pdb_id[1:3]

    url = (
        f"https://files.rcsb.org/pub/pdb/validation_reports/"
        f"{middle}/{pdb_id}/{pdb_id}_full_validation.xml.gz"
    )

    r = requests.get(url)
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


# Extract mmCIF metadata
def extract_cif_metadata(cif_file):
    d = MMCIF2Dict(cif_file)

    def g(key):
        v = d.get(key)
        if isinstance(v, list):
            return v[0] if v else None
        return v

    return {
        "title": g("_struct.title"),
        "method": g("_exptl.method"),
        "resolution": g("_refine.ls_d_res_high") or g("_em_3d_reconstruction.resolution"),
        "deposition_date": g("_pdbx_database_status.recvd_initial_deposition_date"),
    }


# Extract validation metrics
def extract_validation(xml_file):
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


# Process single entry
def process_pdb(pdb_id, outdir):
    cif = download_mmcif(pdb_id, outdir)
    meta = extract_cif_metadata(cif)

    xml = download_validation_xml(pdb_id, outdir)
    val = extract_validation(xml) if xml else {}

    return {
        "pdb_id": pdb_id.upper(),
        **meta,
        **val
    }


# Output table
def print_table(rows):
    headers = rows[0].keys()

    print("\n" + "\t".join(headers))
    print("-" * 80)

    for r in rows:
        print("\t".join(str(r.get(h, "")) for h in headers))


# Output CSV
def write_csv(rows, filename):
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

# Main CLI
def main():
    parser = argparse.ArgumentParser(
        description="RCSB-style PDB Validation CLI Tool"
    )

    parser.add_argument(
        "pdb_ids",
        nargs="+",
        help="One or more PDB IDs"
    )

    parser.add_argument(
        "--out",
        default="pdb_data",
        help="Output directory"
    )

    parser.add_argument(
        "--csv",
        help="Write results to CSV file"
    )

    args = parser.parse_args()

    outdir = Path(args.out)
    outdir.mkdir(exist_ok=True)

    results = []

    for pdb_id in args.pdb_ids:
        print(f"Processing {pdb_id}...")
        try:
            result = process_pdb(pdb_id, outdir)
            results.append(result)
        except Exception as e:
            print(f"Failed {pdb_id}: {e}")

    if not results:
        print("No valid entries processed.")
        return

    print_table(results)

    if args.csv:
        write_csv(results, args.csv)
        print(f"\nCSV written to: {args.csv}")


if __name__ == "__main__":
    main()
