import pandas as pd #for data manipulation
import urllib.request #for downloading data from clinvar
import gzip #for unzipping downloaded data
import json #for parsing json data

# Temp genes to check for
GENES_CHECKED = {"BRCA1", "BRCA2", "TP53", "CFTR"}

# ClinVar data source and output file
CLINVAR_URL = "https://ftp.ncbi.nlm.nih.gov/pub/clinvar/tab_delimited/variant_summary.txt.gz"
OUTPUT_FILE = "clinvar_filtered.json"

# Function to download, process, and filter ClinVar data
def download_and_process_clinvar():

    # Download the gzipped file
    print("Downloading ClinVar data...")
    urllib.request.urlretrieve(CLINVAR_URL, "variant_summary.txt.gz")

    # Read the gzipped file into a pandas DataFrame
    print("Processing ClinVar data...")
    # open compressed file without fully uncompressing to save space
    with gzip.open("variant_summary.txt.gz", "rt", encoding="utf-8") as f:
        df = pd.read_csv(f, sep="\t", low_memory=False) # columns separated by tabs, low_memory to avoid  warnings


    # Filter for variants in the specified genes
    print("Filtering for specified genes...")
    filtered = df[df["GeneSymbol"].isin(GENES_CHECKED)]

    columns_kept = [
        "GeneSymbol", 
        "Name", 
        "ClinicalSignificance", 
        "ReviewStatus", 
        "PhenotypeList", 
        "Assembly", 
        "VariationID"
    ]

    filtered = filtered[columns_kept]

    #remove incomplete entries
    filtered = filtered.dropna(subset=["GeneSymbol", "ClinicalSignificance"])

    # convert pandas table to list of dictionaries for JSON
    records = filtered.to_dict("records")

    # Save the filtered data to a JSON file
    with open(OUTPUT_FILE, "w") as f:
        json.dump(records, f, indent=2)

    print(f"Done. Saved {len(records)} records to {OUTPUT_FILE}.")

# Run when scipt is executed directly
if __name__ == "__main__":
    download_and_process_clinvar()