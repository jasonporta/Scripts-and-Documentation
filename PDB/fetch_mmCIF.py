from Bio.PDB import PDBList
import requests
from pathlib import Path

# Script that will fetch an mmCIF file from the RCSB PDB. Input accepts
# 4-character PDB IDs and the new extended format IDs. Can input IDs
# using either upper or lower case characters

def download_mmcif(pdb_id, output_dir="."):
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)

    # In case of spaces
    pdb_id = pdb_id.strip()

    # Process 4-character PDB ID
    if len(pdb_id) == 4:
        pdb_id = pdb_id.lower()
        pdbl = PDBList()
        filename = pdbl.retrieve_pdb_file(
            pdb_id,
            pdir=str(output_dir),
            file_format="mmCif",
            overwrite=True
        )

        print(f"\nDownloaded successfully:")
        print(filename)
        return filename

    # Process new extended PDB ID
    elif pdb_id.upper().startswith("PDB_"):
        pdb_id = pdb_id.upper()

        short_id = pdb_id[-4:].lower()
        url = f"https://files.rcsb.org/download/{short_id}.cif"
        output_file = output_dir / f"{pdb_id}.cif"
        response = requests.get(url)

        if response.status_code == 200:
            with open(output_file, "wb") as f:
                f.write(response.content)
            print(f"\nDownloaded successfully:")
            print(output_file)
            return str(output_file)

        else:
            raise ValueError(
                f"Could not download structure for: {pdb_id}"
            )

    else:
        raise ValueError(
            "\nInvalid input.\n"
            "Use either:\n"
            "  - a 4-character PDB ID\n"
            "  - or an extended ID like PDB_00001ABC\n"
        )

pdb_input = input(
    "Enter the PDB code using either the old "
    "4-character ID or new extended ID: "
)

download_mmcif(pdb_input)
