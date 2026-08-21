import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import MerchantForm from './components/MerchantForm';
import RiskCards from './components/RiskCards';
import ClaimVsEvidence from './components/ClaimVsEvidence';
import EvidenceGrid from './components/EvidenceGrid';
import HeatmapViewer from './components/HeatmapViewer';
import { analyzeMerchant } from './api/client';
import { AlertCircle } from 'lucide-react';

export default function App() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleAnalyze = async (formData) => {
    setLoading(true);
    setError(null);
    try {
      const data = await analyzeMerchant(formData);
      setResult(data);
    } catch (err) {
      console.error('Error analyzing merchant:', err);
      setError(err.message || 'Analysis failed. Make sure backend is running.');
    } finally {
      setLoading(false);
    }
  };

  // Initial load default demo case
  useEffect(() => {
    const initForm = new FormData();
    initForm.append('mode', 'demo');
    initForm.append('demo_case', 'Suspicious Merchant');
    handleAnalyze(initForm);
  }, []);

  return (
    <div className="app-container">
      <Header />

      <MerchantForm onAnalyze={handleAnalyze} loading={loading} />

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
            <strong>Analysis Request Failed:</strong> {error}
          </div>
        </div>
      )}

      {result && (
        <>
          <RiskCards fusion={result.fusion} />

          <ClaimVsEvidence
            claims={result.claims}
            reuse={result.reuse}
            logo={result.logo}
            manipulation={result.manipulation}
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
        <p>🛡️ Visual Consistency & Evidence Engine • Razorpay AI Risk Manager Track Submission</p>
        <p style={{ marginTop: '0.25rem' }}>
          Decision Support Prototype for Human Risk Analysts — Never automatically rejects merchants.
        </p>
      </footer>
    </div>
  );
}
