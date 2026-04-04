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
  notes: string;
}

export default function Home() {
  
  //store variables for gene, variant, and result of analysis between front and back
  const [gene, setGene] = useState("");
  const [variant, setVariant] = useState("");
  const [result, setResult] = useState<VariantResult | null>(null);

  //funtion to call backend and store results of analysis
  const handleSubmit = async () => { //async to allow for waiting for backend
    const response = await fetch("http://localhost:8000/variant/predict", {
      method: "POST", //backend fetch expects POST
      headers: {
        "Content-Type": "application/json", //data is in JSON format
      },
      body: JSON.stringify({ gene, variant }), //converts JS object to JSON string
    });

    const data = await response.json();
    setResult(data);
  };

  return (
    <main className="min-h-screen bg-grey-50 flex flex-col items-center justify-center p-8">
      
      {/* Header and description */}
      <h1 className="text-4xl font-bold text-grey-900 mb-2">GeneVariance AI</h1>
      <p className="text-grey-500 mb-8">Enter a genetic variant to get a pathogenicity prediction</p>

      {/* Container for Input form for gene and variant */}
      <div className="bg-white rounded=x1 shadow p-8 w-full max-w-md">
        
        {/* Gene name input */}
        <div className = "mb-4">
          <label className="block text-sm front-medium text-grey-700 mb-1">Gene</label>
          <input
            type="text"
            placeholder="e.g. BRCA1"
            value = {gene}
            onChange={(e) => setGene(e.target.value)}
            className="w-full border border-grey-300 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />  
        </div>

        {/* Variant input */}
        <div className="mb-6">
          <label className = "block text-sm font-medium text-grey-700 mb-1">Variant</label>
          <input
            type="text"
            placeholder="e.g. A1708E"
            value={variant}
            onChange={(e) => setVariant(e.target.value)}
            className="w-full border border-grey-300 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Button to trigger analysis of variant */}
        <button 
          onClick={handleSubmit}
          className = "w-full bg-blue-600 text-white font-semibold py-2 rounded-lg hover:bg-blue-700 transition"
        >
            Analyze Variant
        </button>
      </div>

      {/* Results Container that only shows when result is available */}
      {result && (
        <div className = "mt-6 p-4 bg-grey-50 rounded-lg border border-grey-200">
          <p className = "text-sm font-semibold text-gray-700">Classification: {result.classification}</p>
          <p className = "text-sm text-gray-500">Confidence: {result.confidence}</p>
          <ul className = "mt-2 text-sm text-grey-600 list-disc list-inside"> {/* list of evidence */}
            {result.evidence.map((item, index) => (
              <li key={index}>{item}</li>
            ))}
          </ul>
          {result.notes && (
            <p className = "text-sm text-grey-600 mt-2">Notes: {result.notes}</p>
          )}
        </div>
      )}
    </main>
  );
}
