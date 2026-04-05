import json
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report
import xgboost as xgb
import joblib

# Function to load and preprocess ClinVar data for model training
def load_clinvar_data():
    with open("clinvar_filtered.json", "r") as f:
        data = json.load(f)
    

    # Convert the list of dictionaries to a pandas DataFrame
    df = pd.DataFrame(data)

    # Map the ClinicalSignificance to numerical labels for model training
    label_map = {
        "Benign": 0,
        "Likely benign": 0,
        "Benign/Likely benign": 0,
        "Uncertain significance": 1,
        "Likely pathogenic": 2,
        "Pathogenic": 2,
        "Pathogenic/Likely pathogenic": 2,
    }

    # Create a new column 'Label' based on the mapping and drop rows with unmapped values
    df["label"] = df["ClinicalSignificance"].map(label_map)
    df = df.dropna(subset=["label"])

    return df


# Function to engineer features from the ClinVar data for model training
def engineer_features(df):

    # Encode the gene symbol as a categorical variable
    gene_encoder = LabelEncoder()
    df["gene_encoded"] = gene_encoder.fit_transform(df["GeneSymbol"])

    # Encode the review status as a numerical score based on the level of review
    review_status_score = {
        "practice guideline": 4,
        "reviewed by expert panel": 3,
        "criteria provided, multiple submitters, no conflicts": 2,
        "criteria provided, single submitter": 1,
        "no assertion criteria provided": 0,
        "no assertion provided": 0,
    }
    # create a new column 'review_score' based on the mapping and fill unmapped values with 0
    df["review_score"] = df["ReviewStatus"].map(review_status_score).fillna(0)

    # Extract referenc amino acids from the variant name (if available)
    def extract_ref(name):

        if "p." in str(name):
            protein = name.split("p.")[-1].strip(")") # get the part after "p." and remove any trailing parentheses
            return protein[:3] if len(protein) >= 3 else "Unk" # return the first 3 characters as the reference amino acid, or "Unk" if not available
        return "Unk"
    
    # Extract alternate amino acids from the variant name (if available)
    def extract_alt(name):
        if "p." in str(name):
            protein = name.split("p.")[-1].strip(")")
            return protein[-3:] if len(protein) >= 3 else "Unk"
        return "Unk"
    
    # apply the extraction functions to create new columns for reference and alternate amino acids
    df["ref_aa"] = df["Name"].apply(extract_ref)
    df["alt_aa"] = df["Name"].apply(extract_alt)

    aa_encoder = LabelEncoder()
    all_aas = pd.concat([df["ref_aa"], df["alt_aa"]])
    aa_encoder.fit(all_aas)
    # encode the reference and alternate amino acids using the fitted encoder
    df["ref_aa_encoded"] = aa_encoder.transform(df["ref_aa"])
    df["alt_aa_encoded"] = aa_encoder.transform(df["alt_aa"])

    # Select the engineered features for model training
    features = df[["gene_encoded", "review_score", "ref_aa_encoded", "alt_aa_encoded"]]

    return features, df["label"], gene_encoder, aa_encoder

# Main function to train the model
def train():

    df = load_clinvar_data()

    # engineer features and labels for model training
    # X is features and y is labels
    X, y, gene_encoder, aa_encoder = engineer_features(df)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=3)
    
    # model specifications
    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.1,
        num_class=3,
        objective="multi:softmax",
        eval_metric="mlogloss",
        use_label_encoder=False,
    )

    # Train the model on the training data
    model.fit(X_train, y_train)

    # Evaluate the model on the test set and print a classification report
    y_pred = model.predict(X_test)
    print(classification_report(y_test, y_pred, target_names=["Benign", "Uncertain", "Pathogenic"]))

    # Save the trained model and encoders to disk for later use in the backend API
    joblib.dump(model, "variant_model.pkl")
    joblib.dump(gene_encoder, "gene_encoder.pkl")
    joblib.dump(aa_encoder, "aa_encoder.pkl")

    print("Model saved to variant_model.pkl")

if __name__ == "__main__":
    train()

