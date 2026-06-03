import gemmi

def convert_to_mtz(input_cif_file, output_mtz_file):
    # Read the mmCIF structure factor file
    cif_doc = gemmi.cif.read(input_cif_file)
    
    # Convert the CIF document to a Merger block (handles merged reflection data)
    # The default specs work for standard merged structure factors.
    mtz = gemmi.CifToMtz(cif_doc)
    
    # Write the MTZ file
    mtz.write_to_file(output_mtz_file)
    print(f"Successfully converted {input_cif_file} to {output_mtz_file}")

# Example usage
convert_to_mtz("3K9S-sf.cif", "3K9S.mtz")

