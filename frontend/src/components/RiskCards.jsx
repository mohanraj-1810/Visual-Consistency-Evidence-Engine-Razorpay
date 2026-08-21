import React from 'react';
import { AlertTriangle, CheckCircle2, ShieldCheck, HelpCircle } from 'lucide-react';

export default function RiskCards({ fusion }) {
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
    <div style={{ marginBottom: '2rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
        <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#f8fafc' }}>
          📋 Merchant Profile: <span style={{ color: '#60a5fa' }}>{fusion.merchant_name}</span>
        </h3>
        <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
          Multimodal Decision Support Metric
        </span>
      </div>

      <div className="risk-cards-grid">

      
        {/* Card 1: Text Risk */}
        <div className="risk-card">
          <div className="risk-card-header">Simulated Text / Business Risk</div>
          <div>
            <div className="risk-score-value" style={{ color: '#60a5fa' }}>
              {textScore} <span className="risk-score-denom">/ 100</span>
            </div>
            <div className="risk-card-footer">Website Disclosures & Metadata</div>
          </div>
          <div style={{ fontSize: '0.72rem', color: '#64748b', marginTop: '0.5rem' }}>
            Terms, policies, contact validity
          </div>
        </div>

        {/* Card 2: Visual Evidence Risk */}
        <div className="risk-card">
          <div className="risk-card-header">Visual Evidence Risk</div>
          <div>
            <div className="risk-score-value" style={{ color: visualColor }}>
              {visualScore} <span className="risk-score-denom">/ 100</span>
            </div>
            <div className="risk-card-footer">ViT & Forensic Evidence</div>
          </div>
          <div style={{ fontSize: '0.72rem', color: '#64748b', marginTop: '0.5rem' }}>
            Reuse, tampering, logo drift
          </div>
        </div>

        {/* Card 3: Final Fused Risk */}
        <div className="risk-card" style={{ border: `2px solid ${finalColor}` }}>
          <div className="risk-card-header" style={{ color: '#f8fafc', fontWeight: 800 }}>
            Final Fused Risk
          </div>
          <div>
            <div className="risk-score-value" style={{ color: finalColor }}>
              {finalScore} <span className="risk-score-denom">/ 100</span>
            </div>
            <div className="risk-card-footer" style={{ color: '#e2e8f0', fontWeight: 600 }}>
              Multimodal Weighted Fusion
            </div>
          </div>
          <div style={{ fontSize: '0.72rem', color: '#94a3b8', marginTop: '0.5rem' }}>
            Deceptive contrast weighted
          </div>
        </div>

        {/* Card 4: Status Classification Badge */}
        <div className="risk-card" style={{ justifyContent: 'center', background: '#0f172a' }}>
          <div className="risk-card-header">Status Classification</div>
          <div style={{ margin: '0.6rem 0' }}>
            <span className="status-badge" style={{ backgroundColor: finalColor }}>
              {statusLabel}
            </span>
          </div>
          <div style={{ fontSize: '0.82rem', color: '#cbd5e1', lineHeight: '1.4' }}>
            {recommendation}
          </div>
        </div>
      </div>
    </div>
  );
}
