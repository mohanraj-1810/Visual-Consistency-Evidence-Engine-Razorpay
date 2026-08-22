import React, { useState } from 'react';
import Header from './components/Header';
import MerchantForm from './components/MerchantForm';
import RiskCards from './components/RiskCards';
import ClaimVsEvidence from './components/ClaimVsEvidence';
import EvidenceGrid from './components/EvidenceGrid';
import HeatmapViewer from './components/HeatmapViewer';
import { streamWebsiteAnalysis } from './api/client';
import { AlertCircle } from 'lucide-react';

export default function App() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [currentSteps, setCurrentSteps] = useState({});

  const handleAnalyze = (url) => {
    setLoading(true);
    setError(null);
    setCurrentSteps({});

    const closeStream = streamWebsiteAnalysis(
      url,
      (stepEvent) => {
        setCurrentSteps((prev) => ({
          ...prev,
          [stepEvent.step]: stepEvent.status,
        }));
      },
      (analysisData) => {
        setCurrentSteps((prev) => ({ ...prev, all_done: true }));
        setResult(analysisData);
        setLoading(false);
      },
      (err) => {
        console.error('Analysis error:', err);
        setError(err.message || 'Analysis failed. Make sure backend is running.');
        setLoading(false);
      }
    );

    return closeStream;
  };

  return (
    <div className="app-container">
      <Header />

      <MerchantForm onAnalyze={handleAnalyze} loading={loading} currentSteps={currentSteps} />

      {error && (
        <div
          style={{
            background: 'rgba(239, 68, 68, 0.15)',
            border: '1px solid #ef4444',
            color: '#fca5a5',
            padding: '1rem 1.25rem',
            borderRadius: '8px',
            marginBottom: '1.5rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem',
          }}
        >
          <AlertCircle size={20} color="#ef4444" style={{ flexShrink: 0 }} />
          <div>
            <strong>Analysis Notice:</strong> {error}
          </div>
        </div>
      )}

      {result && (
        <>
          <RiskCards fusion={result.fusion} claims={result.claims} />

          <ClaimVsEvidence
            claimsReasoning={result.claims_reasoning}
            structuredEvidence={result.structured_evidence}
            claims={result.claims}
          />

          <EvidenceGrid
            reuse={result.reuse}
            logo={result.logo}
            manipulation={result.manipulation}
            identity={result.identity}
          />

          <HeatmapViewer result={result} />
        </>
      )}

      <footer
        style={{
          marginTop: '3rem',
          paddingTop: '1.5rem',
          borderTop: '1px solid #334155',
          textAlign: 'center',
          color: '#64748b',
          fontSize: '0.8rem',
        }}
      >
        <p>🛡️ Visual Risk Intelligence Engine • Razorpay AI Risk Manager</p>
        <p style={{ marginTop: '0.25rem' }}>
          Decision Support System for Human Risk Analysts — Never automatically rejects merchants.
        </p>
      </footer>
    </div>
  );
}
