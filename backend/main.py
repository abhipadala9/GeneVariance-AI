from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Create FastAPI app
app = FastAPI(title = "GeneVariance AI API", version="0.1.0")

# Set up CORS middleware to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    # Placeholder response - in a real implementation, this would run a machine learning model
    return {
        "gene": variant_request.gene.upper(),
        "variant": variant_request.variant,
        "classification": "benign",  # This is a dummy classification
        "confidence": 0.95,  # This is a dummy confidence score
        "evidence": [
            "Test1",
            "Test2",
            "Test3"
        ],
        "notes": "This is a placeholder prediction. Replace with actual model output.",
    }