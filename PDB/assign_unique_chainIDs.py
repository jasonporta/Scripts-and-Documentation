import gemmi
import string

# Generate unique chain identifiers for overcoming the
# 62 unique chain ID limitation in Coot
def generate_ids():
    singles = list(string.ascii_uppercase + string.ascii_lowercase + string.digits)
    for s in singles:
        yield s
    for a in string.ascii_uppercase:
        for b in string.ascii_uppercase:
            yield a + b

# Put the coordinates file here
st = gemmi.read_structure("dummy_88chains.pdb", merge_chain_parts=False)

# Invoke the function and change the chain IDs
id_gen = generate_ids()
for chain in st[0]:
    chain.name = next(id_gen)

# Verify it worked correctly by printing to STDOUT
names = [chain.name for chain in st[0]]
print(f"Total chains: {len(names)}")
print(f"Unique chains: {len(set(names))}")
print(f"All unique: {len(names) == len(set(names))}")

# Write out the new file in mmCIF format
st.make_mmcif_document().write_file("output.cif")
