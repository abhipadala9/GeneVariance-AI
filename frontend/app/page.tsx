"use client";
//Next.js runs in bowser to allow for interactivity

import { useState } from "react";

//structure of the result returned from backend after analysis
interface VariantResult {
  gene: string;
  variant: string;
  classification: string;
  confidence: number;
  evidence: string[];
  papers: { title: string; journal: string; year: string; url: string }[];
  explanation: {feature: string; value: number }[];
  notes: string;
}

export default function Home() {
  
  //store variables for gene, variant, and result of analysis between front and back
  const [gene, setGene] = useState("");
  const [variant, setVariant] = useState("");
  const [result, setResult] = useState<VariantResult | null>(null);
  const [loading, setLoading] = useState(false);

  //funtion to call backend and store results of analysis
  const handleSubmit = async () => { //async to allow for waiting for backend
    setLoading(true);
    const response = await fetch("http://localhost:8000/variant/predict", {
      method: "POST", //backend fetch expects POST
      headers: {
        "Content-Type": "application/json", //data is in JSON format
      },
      body: JSON.stringify({ gene, variant }), //converts JS object to JSON string
    });

    const data = await response.json();
    setResult(data);
    setLoading(false);
  };

  //function to determine color of classification text based on the classification result
  //use .includes since we can have likely as a prefix
  const getClassificationColor = (classification: string) => {
    if (classification.toLowerCase().includes("pathogenic")) return "text-red-600";
    if (classification.toLowerCase().includes("benign")) return "text-green-600";
    if (classification.toLowerCase().includes("uncertain")) return "text-yellow-600";
    return "text-gray-600";
  }

  return (
    <main className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-8">
      
      {/* Header and description */}
      <h1 className="text-4xl font-bold text-gray-900 mb-2">GeneVariance AI</h1>
      <p className="text-gray-500 mb-8">Enter a genetic variant to get a pathogenicity prediction</p>

      {/* Container for Input form for gene and variant */}
      <div className="bg-white rounded-xl shadow p-8 w-full max-w-md">
        
        {/* Gene name input */}
        <div className = "mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">Gene</label>
          <input
            type="text"
            placeholder="e.g. BRCA1"
            value = {gene}
            onChange={(e) => setGene(e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />  
        </div>

        {/* Variant input */}
        <div className="mb-6">
          <label className = "block text-sm font-medium text-gray-700 mb-1">Variant</label>
          <input
            type="text"
            placeholder="e.g. A1708E"
            value={variant}
            onChange={(e) => setVariant(e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Button to trigger analysis of variant */}
        <button 
          onClick={handleSubmit}
          disabled = {loading}
          className = "w-full bg-blue-600 text-white font-semibold py-2 rounded-lg hover:bg-blue-700 transition disabled:opacity-50"
        >
          {loading ? "Analyzing..." : "Analyze Variant"}
        </button>
      </div>

      {/* Results Container that only shows when result is available */}
      {result && (
        <div className = "mt-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
          <p className = {`text-sm font-semibold ${getClassificationColor(result.classification)}`}>
            Classification: {result.classification}
          </p>
          {/* Confidence score of the prediction */}
          <div className = "mt-1 mb-2">
            <p className = "text-sm text-gray-500">Confidence: {(result.confidence * 100).toFixed(0)}%</p>
            <div className = "w-full bg-gray-200 rounded-full h-2 mt-1">
              <div
                className = "bg-blue-600 h-2 rounded-full"
                style={{ width: `${result.confidence * 100}%` }}
              ></div>
            </div>
          </div>
          <ul className = "mt-2 text-sm text-gray-600 list-disc list-inside"> {/* list of evidence */}
            {result.evidence.map((item, index) => (
              <li key={index}>{item}</li>
            ))}
          </ul>

          {/* List of related research papers if available */}
          <div className="mt-3">
            <p className="text-sm font-semibold text-gray-700">Related Research</p>
            {result.papers && result.papers.length > 0 ? (
              <ul className="mt-1 text-sm text-blue-600 list-disc list-inside">
                {result.papers.map((paper, index) => (
                  <li key={index}>
                    <a href={paper.url} target="_blank" rel="noopener noreferrer">
                      {paper.title} - {paper.journal} ({paper.year})
                    </a>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="mt-1 text-sm text-gray-500">No published literature found for this specific variant.</p>
            )}
          </div>

          {/* SHAP explanation of feature contributions to the model's prediction if available */}
          {result.explanation && result.explanation.length > 0 && (
            <div className = "mt-3">
              <p className = "text-sm font-semibold text-gray-700">How is the prediction determined</p>
              <ul className = "mt-1 text-sm text-gray-600 list-disc list-inside">
                {result.explanation.map((item, index) => (
                  <li key={index}>
                    {item.feature}: {item.value > 0 ? "+" : ""}{item.value.toFixed(3)} 
                  </li>
                ))}
              </ul>
            </div>
           )}

          {result.notes && (
            <p className = "text-sm text-gray-600 mt-2">Notes: {result.notes}</p>
          )}
        </div>
      )}
    </main>
  );
}
