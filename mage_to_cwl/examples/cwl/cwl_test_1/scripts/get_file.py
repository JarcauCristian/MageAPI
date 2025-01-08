import os
import pandas as pd
import requests

if __name__ == "__main__":
    url = "https://raw.githubusercontent.com/zaneveld/full_spectrum_bioinformatics/master/content/06_biological_sequences/Human_FMR1_Protein_UniProt.fasta"
    response = requests.request("GET", url)
    result = "\n".join([entry[::-1] for entry in response.text.split("\n")])
    output_file = os.getenv("GET_FILE_OUTPUT_FILE")
    if output_file:
        with open(output_file, "wb") as file:
            import pickle

            pickle.dump(result, file)
