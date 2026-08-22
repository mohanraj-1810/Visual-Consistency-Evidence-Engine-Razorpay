import React from 'react';
import { Scale, ShoppingBag, Award, FileCheck2, AlertTriangle, CheckCircle2, HelpCircle, ShieldAlert, Globe, Database } from 'lucide-react';

export default function ClaimVsEvidence({ claimsReasoning, structuredEvidence, claims }) {
  const claimItems = claimsReasoning?.claim_items || [];
  const conclusion = claimsReasoning?.conclusion || "Visual evidence is consistent across products and matches claimed merchant branding.";
  const recommendation = claimsReasoning?.recommendation || "Standard merchant onboarding flow; automated monitoring enabled.";

  const getRelationshipBadge = (relationship) => {
    switch (relationship) {
      case 'CONTRADICTS':
        return {
          icon: <AlertTriangle size={15} color="#ef4444" />,
          label: 'CONTRADICTS',
          bgColor: 'rgba(239, 68, 68, 0.15)',
          borderColor: '#ef4444',
          textColor: '#f87171',
        };
      case 'REQUIRES_VERIFICATION':
        return {
          icon: <HelpCircle size={15} color="#f59e0b" />,
          label: 'REQUIRES VERIFICATION',
          bgColor: 'rgba(245, 158, 11, 0.15)',
          borderColor: '#f59e0b',
          textColor: '#fbbf24',
        };
      case 'SUPPORTS':
      default:
        return {
          icon: <CheckCircle2 size={15} color="#10b981" />,
          label: 'SUPPORTS',
          bgColor: 'rgba(16, 185, 129, 0.15)',
          borderColor: '#10b981',
          textColor: '#34d399',
        };
    }
  };

  const getDimensionIcon = (dim) => {
    if (dim.includes('1') || dim.toLowerCase().includes('inventory')) {
      return <ShoppingBag size={18} color="#60a5fa" />;
    }
    if (dim.includes('2') || dim.toLowerCase().includes('brand') || dim.toLowerCase().includes('logo')) {
      return <Award size={18} color="#a855f7" />;
    }
    return <FileCheck2 size={18} color="#10b981" />;
  };

  return (
    <div style={{ marginBottom: '2.5rem' }}>
      <div style={{ marginBottom: '1.25rem', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div>
          <h3 style={{ fontSize: '1.3rem', fontWeight: 800, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Scale size={22} color="#6366f1" />
            Claim ↔ Visual Evidence Reasoning Layer
          </h3>
          <p style={{ fontSize: '0.86rem', color: '#94a3b8', marginTop: '0.2rem' }}>
            Core question: <em>«Does the visual evidence associated with this merchant support or contradict what they claim?»</em>
          </p>
        </div>
      </div>

      {/* Side-by-Side Matrix Grid */}
      <div className="matrix-grid">
        {claimItems.map((item, idx) => {
          const badge = getRelationshipBadge(item.relationship);
          const isOnline = item.source_type === 'ONLINE';

          return (
            <div key={idx} className="matrix-col">
              <h4>
                {getDimensionIcon(item.dimension)}
                {item.dimension}
              </h4>

              {/* Merchant Claim Box */}
              <div className="claim-box">
                <div className="claim-box-title">Merchant Claim</div>
                <div className="claim-box-content">"{item.claim}"</div>
              </div>

              {/* Visual Evidence Finding Box */}
              <div
                className="reality-box"
                style={{
                  background: badge.bgColor,
                  border: `1px solid ${badge.borderColor}`,
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    marginBottom: '0.4rem',
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.35rem',
                      fontWeight: 700,
                      fontSize: '0.78rem',
                      color: badge.textColor,
                    }}
                  >
                    {badge.icon}
                    {badge.label}
                  </div>

                  <span
                    style={{
                      fontSize: '0.68rem',
                      fontWeight: 600,
                      padding: '0.15rem 0.4rem',
                      borderRadius: '4px',
                      background: isOnline ? 'rgba(59, 130, 246, 0.25)' : 'rgba(100, 116, 139, 0.25)',
                      color: isOnline ? '#93c5fd' : '#cbd5e1',
                      border: `1px solid ${isOnline ? '#3b82f6' : '#475569'}`,
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.25rem',
                    }}
                  >
                    {isOnline ? <Globe size={11} /> : <Database size={11} />}
                    {isOnline ? 'ONLINE EVIDENCE' : 'LOCAL DEMO REFERENCE'}
                  </span>
                </div>

                <div className="claim-box-content" style={{ color: '#f1f5f9' }}>
                  {item.evidence_summary}
                </div>

                <div style={{ marginTop: '0.5rem', fontSize: '0.75rem', color: '#94a3b8', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontWeight: 600, color: '#cbd5e1' }}>{item.score_label}</span>
                  {item.source_domain && (
                    <span style={{ fontStyle: 'italic' }}>
                      Source: {item.source_domain}
                    </span>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Dynamic Conclusion & Recommendation Synthesis Banner */}
      <div
        style={{
          marginTop: '1.25rem',
          background: 'linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%)',
          border: '1px solid #4338ca',
          borderRadius: '10px',
          padding: '1.25rem 1.5rem',
          display: 'grid',
          gridTemplateColumns: '1.5fr 1fr',
          gap: '1.5rem',
          alignItems: 'center',
        }}
      >
        <div>
          <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#a5b4fc', fontWeight: 700, marginBottom: '0.3rem' }}>
            Synthesized Evidence Conclusion
          </div>
          <div style={{ fontSize: '1rem', fontWeight: 600, color: '#f8fafc', lineHeight: '1.4' }}>
            "{conclusion}"
          </div>
        </div>

        <div
          style={{
            borderLeft: '1px solid rgba(99, 102, 241, 0.3)',
            paddingLeft: '1.25rem',
          }}
        >
          <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#cbd5e1', fontWeight: 700, marginBottom: '0.3rem' }}>
            Actionable Analyst Recommendation
          </div>
          <div style={{ fontSize: '0.88rem', fontWeight: 600, color: '#38bdf8' }}>
            {recommendation}
          </div>
        </div>
      </div>
    </div>
  );
}
