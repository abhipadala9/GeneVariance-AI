from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import joblib
import numpy as np
import pandas as pd
import json
import os

# Create FastAPI app
app = FastAPI(title = "GeneVariance AI API", version="0.1.0")

# Set up CORS middleware to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Clinvar data from JSON file created by clinvar_parser.py
CLINVAR_DATA = []

if os.path.exists("clinvar_filtered.json"):
    with open("clinvar_filtered.json", "r") as f:
        CLINVAR_DATA = json.load(f)
    print(f"Loaded {len(CLINVAR_DATA)} records from clinvar_filtered.json")
else:
    print("clinvar_filtered.json not found. Please run clinvar_parser.py to generate the data.")

# Load the trained machine learning model and encoders if they exist
ML_MODEL = None
GENE_ENCODER = None
AA_ENCODER = None

if os.path.exists("variant_model.pkl"):
    ML_MODEL = joblib.load("variant_model.pkl")
    GENE_ENCODER = joblib.load("gene_encoder.pkl")
    AA_ENCODER = joblib.load("aa_encoder.pkl")
    print("Loaded machine learning model and encoders.")
else:
    print("Model files not found. Please run train_model.py first.")


# Mapping of single-letter amino acid codes to full names
AMINO_ACIDS = {
    "A": "Ala",
    "R": "Arg",
    "N": "Asn",
    "D": "Asp",
    "C": "Cys",
    "E": "Glu",
    "Q": "Gln",
    "G": "Gly",
    "H": "His",
    "I": "Ile",
    "L": "Leu",
    "K": "Lys",
    "M": "Met",
    "F": "Phe",
    "P": "Pro",
    "S": "Ser",
    "T": "Thr",
    "W": "Trp",
    "Y": "Tyr",
    "V": "Val",
}


# Function to convert variant notation from single-letter amino acid codes to full names
def convert_variant(variant: str):
    # Simple check to ensure variant is in expected format (e.g., "R175H")
    if (len(variant) < 3): 
        return variant

    # Extract the reference amino acid, position, and alternate amino acid
    ref = AMINO_ACIDS.get(variant[0], variant[0])
    alt = AMINO_ACIDS.get(variant[-1], variant[-1])
    pos = variant[1:-1]

    return f"p.{ref}{pos}{alt}"


# Function to classify a variant based on the loaded ClinVar data
def lookup_variant(gene: str, variant: str):
    
    # Convert the variant to the format used in ClinVar for better matching
    converted = convert_variant(variant) 

    # Search for matches in the ClinVar data based on gene and variant (both original and converted)
    matches = [
        v for v in CLINVAR_DATA
        if v["GeneSymbol"] == gene.upper() 
        and (variant.upper() in v["Name"].upper() or converted.upper() in v["Name"].upper())
    ]
    
    return matches

# labels for model training based on ClinVar clinical significance categories
LABEL_NAMES = {0: "Benign", 1: "Uncertain Significance", 2: "Pathogenic"}

# Function to make a prediction using the machine learning model based on gene and variant input
def ml_predict(gene: str, variant: str):

    # Check if the model is loaded
    if ML_MODEL is None:
        return "Model not available", 0.0
    
    
    try:
        # make gene uppercase and check if it is recognized by the gene encoder
        gene_upper = gene.upper()
        if gene_upper not in GENE_ENCODER.classes_:
            return "Gene not recognized by model", 0.0
        
        # convert gene name to its number
        gene_encoded = GENE_ENCODER.transform([gene_upper])[0]

        #converts string and pulls out three letter amino acid codes
        converted = convert_variant(variant)
        ref_aa = converted[2:5] if converted.startswith("p.") else "Unk"
        alt_aa = converted[-3:] if converted.startswith("p.") else "Unk"

        # safety check to ensure aa are recognized
        if ref_aa not in AA_ENCODER.classes_:
            ref_aa = "Unk"
        if alt_aa not in AA_ENCODER.classes_:
            alt_aa = "Unk"

        #converts aa to numbers for encoder
        ref_encoded = AA_ENCODER.transform([ref_aa])[0]
        alt_encoded = AA_ENCODER.transform([alt_aa])[0]

        # create a feature vector for the model prediction
        features = pd.DataFrame([[gene_encoded, 0, ref_encoded, alt_encoded]], 
                                columns=["gene_encoded", "review_score", "ref_aa_encoded", "alt_aa_encoded"])
        
        # Runs the model prediction and gets the predicted class and confidence score
        prediction = ML_MODEL.predict(features)[0]
        probabilities = ML_MODEL.predict_proba(features)[0]
        confidence = round(float(probabilities[prediction]), 2)

        return LABEL_NAMES[prediction], confidence

    except Exception: # catch any errors during encoding and return a default response
        return "Error processing input", 0.0


# Create blueprint for the data the frontend will send to the backend
class VariantRequest(BaseModel):
    gene: str
    variant: str


#Three endpoints that frontend calls

# Confirm server is running
@app.get("/health")
def health_check():
    return {"status": "ok", "service": "GeneVariance AI"}

# Endpoint to receive variant data from the frontend
@app.get("/gene/{gene_name}")
def get_gene_info(gene_name: str):
    # Placeholder response - in a real implementation, this would query a database or external API
    return {
        "gene": gene_name,
        "description": f"Information about {gene_name} will be here.",
    }

# prediction endpoint to receive variant data and return a prediction
@app.post("/variant/predict")
def predict_variant(variant_request: VariantRequest):
    
    # Look up the variant in the ClinVar data
    matches = lookup_variant(variant_request.gene, variant_request.variant)
    valid_matches = [m for m in matches if m["ClinicalSignificance"] and m["ClinicalSignificance"].strip() not in ["", "-", "not provided"]]

    # If matches are found, select the one with the highest confidence based on review status and phenotype information
    if valid_matches:
        top = sorted(
            valid_matches,
            key = lambda v: ( # prioritize entries with provided phenotype information and higher review status
                v["PhenotypeList"] != "not provided", 
                v["ReviewStatus"] in ["reviewed by expert panel", "criteria provided, multiple submitters, no conflicts"],
            ),
            reverse=True    
        )[0]

        # Map review status to a confidence score for the ClinVar classification
        review_confidence = {
            "practice guideline": 0.99,
            "reviewed by expert panel": 0.95,
            "criteria provided, multiple submitters, no conflicts": 0.85,
            "criteria provided, single submitter": 0.70,
            "no assertion criteria provided": 0.50,
            "no assertion provided": 0.40,
        }

        # Return the ClinVar classification with evidence and confidence score based on the review status and phenotype information
        return {
            "gene": top["GeneSymbol"],
            "variant": variant_request.variant,
            "classification": top["ClinicalSignificance"],
            "confidence": review_confidence.get(top["ReviewStatus"], 0.50),
            "source": "ClinVar database",
            "evidence": [
                f"ClinVar review status: {top['ReviewStatus']}",
                f"Associated condition: {next((p for p in top['PhenotypeList'].split('|') if p.strip() != 'not provided'), 'not provided')}",
                f"ClinVar Variation ID: {top['VariationID']}"
            ],
            "notes": "This classification is based on existing ClinVar data and may not reflect the latest research. Always consult a genetic counselor or specialist for medical advice."
        }
    
    # If no exact matches are found in ClinVar, attempt to provide a prediction using the machine learning model based on gene and variant features
    ml_classification, ml_confidence = ml_predict(variant_request.gene, variant_request.variant)

    # If the machine learning model provides a classification, return it with evidence and confidence score based on the model's prediction
    if ml_classification:
        return {
            "gene": variant_request.gene,
            "variant": variant_request.variant,
            "classification": ml_classification,
            "confidence": ml_confidence,
            "source": "Machine Learning Model Prediction",
            "evidence": [
                "No exact match found in ClinVar database",
                "Classification based on gene, amino acid change, and learned patterns from ClinVar data",
                "This prediction should be used as supplementary information and not as a definitive classification."
            ],
            "notes": "This classification is based on a machine learning model trained on ClinVar data. It is intended to provide additional insights but should not be used as a sole basis for medical decisions. Always consult a genetic counselor or specialist for medical advice."
        }
    

    # If no matches are found, return a default response indicating the variant was not found
    if not matches:
        return {
            "gene": variant_request.gene,
            "variant": variant_request.variant,
            "classification": "Unable to classify",
            "confidence": 0.0,
            "source": "No data available",
            "evidence": ["No matching variants found in ClinVar data. and machine learning model could not provide a prediction."],
            "notes": "Double check the gene symbol and variant notation. Consider using HGVS format"
        }
    


   