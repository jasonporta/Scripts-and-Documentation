from Bio.PDB.MMCIF2Dict import MMCIF2Dict
from Bio.PDB import PDBList
from pathlib import Path
import xml.etree.ElementTree as ET
import requests
import gzip

# Extracts information about a structure deposited to the
# RCSB PDB including validation statistics from XML file

# Process extended PDB ID
def to_canonical_pdb_id(pdb_id):
    pdb_id = pdb_id.strip().lower()
    if pdb_id.startswith("pdb_"):
        return pdb_id.split("_")[-1][-4:]
    return pdb_id

# Download mmCIF file
def download_mmcif(pdb_id, output_dir="."):
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    pdb_id = pdb_id.strip().lower()
    url = f"https://files.rcsb.org/download/{pdb_id}.cif"
    print(f"Downloading mmCIF:\n{url}")
    r = requests.get(url)

    if r.status_code != 200:
        print(f"Download failed: HTTP {r.status_code}")
        return None

    file_path = output_dir / f"{pdb_id}.cif"
    file_path.write_bytes(r.content)
    return str(file_path)

def get_first(data_dict, key):
    value = data_dict.get(key, ["Not available"])
    
    if isinstance(value, list):
        return value[0]
    return value

# Extract metadata from mmCIF file
def extract_metadata(cif_file):
    mmcif_dict = MMCIF2Dict(cif_file)

    print("\n==============================")
    print("PDB / EMDB METADATA SUMMARY")
    print("==============================\n")

    # Basic Structure Information
    print(f"PDB ID: {get_first(mmcif_dict, '_entry.id')}")
    print(f"Title: {get_first(mmcif_dict, '_struct.title')}")
    print(
        f"Experimental Method: "
        f"{get_first(mmcif_dict, '_exptl.method')}"
    )
    print(
        f"Resolution: "
        f"{get_first(mmcif_dict, '_em_3d_reconstruction.resolution')} Å"
    )
    print(
        f"Deposition Date: "
        f"{get_first(mmcif_dict, '_pdbx_database_status.recvd_initial_deposition_date')}"
    )
    
    # Author list
    authors = mmcif_dict.get(
        '_audit_author.name',
        ["Not available"]
    )
    print("\nAuthors:")

    for author in authors:
        print(f"  - {author}")

    # Organism
    organism = get_first(
        mmcif_dict,
        '_entity_src_nat.pdbx_organism_scientific'
    )

    if organism == "Not available":
        organism = get_first(
            mmcif_dict,
            '_entity_src_gen.pdbx_gene_src_scientific_name'
        )
    print(f"\nOrganism: {organism}")

    # EMDB ID
    emdb_id = get_first(
        mmcif_dict,
        '_pdbx_database_related.db_id'
    )
    print(f"EMDB ID: {emdb_id}")

    # Ligands
    ligands = mmcif_dict.get(
        '_chem_comp.id',
        []
    )

    # Remove standard residues
    standard_residues = {
        'ALA', 'ARG', 'ASN', 'ASP', 'CYS',
        'GLU', 'GLN', 'GLY', 'HIS', 'ILE',
        'LEU', 'LYS', 'MET', 'PHE', 'PRO',
        'SER', 'THR', 'TRP', 'TYR', 'VAL',
        'A', 'U', 'G', 'C', 'DA', 'DT',
        'DG', 'DC', 'HOH'
    }

    filtered_ligands = sorted(
        set(lig for lig in ligands
            if lig not in standard_residues)
    )
    print("\nLigands:")

    if filtered_ligands:
        for ligand in filtered_ligands:
            print(f"  - {ligand}")
    else:
        print("  None detected")

    # Symmetry
    symmetry = get_first(
        mmcif_dict,
        '_symmetry.space_group_name_H-M'
    )
    print(f"\nSymmetry: {symmetry}")

# Download XML for validation statistics
def download_validation_xml(pdb_id):
    middle = pdb_id[1:3]
    urls = [
        f"https://files.rcsb.org/pub/pdb/validation_reports/{middle}/{pdb_id}/{pdb_id}_full_validation.xml.gz",
        f"https://files.rcsb.org/pub/pdb/validation_reports/{middle}/{pdb_id}/{pdb_id}_validation.xml.gz",
    ]

    for url in urls:
        print(f"Trying:\n{url}")
        response = requests.get(url)

        if response.status_code == 200:
            print("Downloaded validation report.")
            gz_file = f"{pdb_id}.xml.gz"

            with open(gz_file, "wb") as f:
                f.write(response.content)

            xml_file = f"{pdb_id}.xml"

            with gzip.open(gz_file, "rb") as f_in:
                content = f_in.read()

            with open(xml_file, "wb") as f_out:
                f_out.write(content)
            return xml_file

    print("No validation XML found.")
    return None

# Extract validation statistics
def extract_validation_stats(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    entry = root.find("Entry")

    if entry is not None:
        print("\nValidation metrics available in XML:\n")
        for k, v in entry.attrib.items():
            print(f"{k}: {v}")

        print("\nFormatted summary:\n")
        print("Clashscore:", entry.attrib.get("clashscore"))
        print("Ramachandran Outliers:", entry.attrib.get("percent-rama-outliers"))
        print("Rotamer Outliers:", entry.attrib.get("percent-rota-outliers"))
        print("MolProbity Score:", entry.attrib.get("molprobity-score"))

# Main Program
raw_id = input("Enter a PDB ID: ").strip()
pdb_id = to_canonical_pdb_id(raw_id)

# Download mmCIF and get canonical PDB ID back
cif_file = download_mmcif(pdb_id)

# Sanity check
if cif_file is None:
    print("Failed to download mmCIF. Exiting.")
    exit()

# Extract metadata
extract_metadata(cif_file)

# Attempt validation download ONLY for valid PDB IDs
xml_file = download_validation_xml(pdb_id)

# Extract validation if available
if xml_file is not None:
    extract_validation_stats(xml_file)
