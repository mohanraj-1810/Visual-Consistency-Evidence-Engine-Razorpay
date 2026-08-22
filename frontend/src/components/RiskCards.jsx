import React from 'react';
import { AlertTriangle, CheckCircle2, ShieldCheck, HelpCircle, Layers, ShieldAlert, FileText } from 'lucide-react';

export default function RiskCards({ fusion, claims }) {
  if (!fusion) return null;

  const textScore = fusion.text_risk_score ?? 0;
  const visualScore = fusion.visual_risk_score ?? 0;
  const finalScore = fusion.final_risk_score ?? 0;
  const status = fusion.status ?? 'LOW';
  const statusLabel = fusion.status_label ?? 'LOW — NORMAL ONBOARDING';
  const recommendation = fusion.recommendation ?? 'Merchant exhibits normal risk parameters.';
  const badgeColor = fusion.badge_color ?? '#10b981';

  // Dynamic colors
  const visualColor = visualScore >= 70 ? '#ef4444' : visualScore >= 40 ? '#f59e0b' : '#10b981';
  const finalColor = badgeColor;

  return (
    <div style={{ marginBottom: '2.5rem' }}>
      {/* Merchant Overview Header Card */}
      <div
        style={{
          background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
          border: '1px solid #334155',
          borderRadius: '12px',
          padding: '1.25rem 1.5rem',
          marginBottom: '1.25rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
        }}
      >
        <div>
          <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#94a3b8', fontWeight: 600 }}>
            Merchant Entity Under Review
          </div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#f8fafc', margin: '0.15rem 0' }}>
            {fusion.merchant_name}
          </h2>
          {claims?.inventory_claim && (
            <div style={{ fontSize: '0.85rem', color: '#cbd5e1', fontStyle: 'italic', maxWidth: '650px' }}>
              Claim: "{claims.inventory_claim}"
            </div>
          )}
        </div>

        <div style={{ textAlign: 'right' }}>
          <span
            className="status-badge"
            style={{
              backgroundColor: finalColor,
              fontSize: '0.9rem',
              padding: '0.5rem 1.1rem',
              letterSpacing: '0.04em',
              fontWeight: 800,
            }}
          >
            {statusLabel}
          </span>
          <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '0.4rem' }}>
            Explainable Decision Support Metric
          </div>
        </div>
      </div>

      {/* 4 Score Summary Cards */}
      <div className="risk-cards-grid">
        {/* Card 1: Simulated Text Risk */}
        <div className="risk-card">
          <div className="risk-card-header">
            <span style={{ color: '#94a3b8' }}>Simulated Existing Merchant Risk</span>
          </div>
          <div>
            <div className="risk-score-value" style={{ color: '#60a5fa' }}>
              {textScore} <span className="risk-score-denom">/ 100</span>
            </div>
            <div className="risk-card-footer">Website Disclosures & Contact Info</div>
          </div>
          <div style={{ fontSize: '0.72rem', color: '#64748b', marginTop: '0.4rem' }}>
            Prototype simulation of standard merchant risk
          </div>
        </div>

        {/* Card 2: Visual Evidence Risk */}
        <div className="risk-card">
          <div className="risk-card-header">
            <span>Visual Evidence Risk</span>
          </div>
          <div>
            <div className="risk-score-value" style={{ color: visualColor }}>
              {visualScore} <span className="risk-score-denom">/ 100</span>
            </div>
            <div className="risk-card-footer">ViT & Multi-Signal Visual Forensics</div>
          </div>
          <div style={{ fontSize: '0.72rem', color: '#64748b', marginTop: '0.4rem' }}>
            Reuse, tampering, logo variance, coherence
          </div>
        </div>

        {/* Card 3: Final Fused Risk */}
        <div className="risk-card" style={{ border: `2px solid ${finalColor}`, background: 'rgba(15, 23, 42, 0.95)' }}>
          <div className="risk-card-header" style={{ color: '#f8fafc', fontWeight: 800 }}>
            Final Fused Risk Score
          </div>
          <div>
            <div className="risk-score-value" style={{ color: finalColor }}>
              {finalScore} <span className="risk-score-denom">/ 100</span>
            </div>
            <div className="risk-card-footer" style={{ color: '#e2e8f0', fontWeight: 700 }}>
              Evidence-Weighted Multimodal Fusion
            </div>
          </div>
          <div style={{ fontSize: '0.72rem', color: '#94a3b8', marginTop: '0.4rem' }}>
            Visual contradictions override text facade
          </div>
        </div>

        {/* Card 4: Classification & Action */}
        <div className="risk-card" style={{ justifyContent: 'center', background: '#0f172a' }}>
          <div className="risk-card-header">Review Action</div>
          <div style={{ margin: '0.4rem 0' }}>
            <span
              style={{
                display: 'inline-block',
                padding: '0.35rem 0.75rem',
                borderRadius: '6px',
                background: status === 'HIGH' ? 'rgba(239, 68, 68, 0.2)' : status === 'MEDIUM' ? 'rgba(245, 158, 11, 0.2)' : 'rgba(16, 185, 129, 0.2)',
                color: finalColor,
                fontWeight: 700,
                fontSize: '0.85rem',
                border: `1px solid ${finalColor}`,
              }}
            >
              {status === 'HIGH' ? '🚨 Route to Manual Review' : status === 'MEDIUM' ? '⚠️ Request Documentation' : '✅ Standard Onboarding'}
            </span>
          </div>
          <div style={{ fontSize: '0.78rem', color: '#cbd5e1', lineHeight: '1.4' }}>
            {recommendation}
          </div>
        </div>
      </div>
    </div>
  );
}
