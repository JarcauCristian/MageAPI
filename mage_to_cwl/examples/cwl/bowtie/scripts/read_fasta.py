import os
import pandas as pd
import io
import requests

if __name__ == "__main__":
    url = "https://raw.githubusercontent.com/zaneveld/full_spectrum_bioinformatics/master/content/06_biological_sequences/Human_FMR1_Protein_UniProt.fasta"
    response = requests.get(url)
    output_file = os.getenv("READ_FASTA_OUTPUT_FILE")
    if output_file:
        with open(output_file, "wb") as file:
            import pickle

            pickle.dump(response.text, file)
