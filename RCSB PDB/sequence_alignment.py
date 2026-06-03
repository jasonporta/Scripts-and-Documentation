from Bio.Align import PairwiseAligner
import requests

def fetch_fasta(pdb_id, chain=None):
    url = f"https://www.rcsb.org/fasta/entry/{pdb_id}"
    fasta = requests.get(url).text

    sequences = {}
    current_header = None
    current_seq = []

    for line in fasta.splitlines():
        if line.startswith(">"):
            if current_header:
                sequences[current_header] = "".join(current_seq)

            current_header = line
            current_seq = []
        else:
            current_seq.append(line.strip())

    if current_header:
        sequences[current_header] = "".join(current_seq)

    # Return specific chain if requested
    if chain:
        for header, seq in sequences.items():
            if f"Chain {chain}" in header:
                return seq

    # Otherwise return first sequence
    return next(iter(sequences.values()))

seq1 = fetch_fasta("7dc1")
seq2 = fetch_fasta("3k9s", chain="A")

aligner = PairwiseAligner()
aligner.mode = 'global'

alignments = aligner.align(seq1, seq2)

print(alignments[0])
