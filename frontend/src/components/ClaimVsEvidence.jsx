import React from 'react';
import { Scale, ShoppingBag, Award, FileCheck2, AlertTriangle, CheckCircle2, HelpCircle, ShieldAlert, Globe, Database, Sparkles, Check, ArrowRight } from 'lucide-react';

export default function ClaimVsEvidence({ claimsReasoning = {}, structuredEvidence = [], claims = {} }) {
  const claimItems = Array.isArray(claimsReasoning?.claim_items) ? claimsReasoning.claim_items : [];
  const conclusion = claimsReasoning?.conclusion || "Visual evidence is consistent across products and matches claimed merchant branding.";
  const recommendation = claimsReasoning?.recommendation || "Standard merchant onboarding flow; automated monitoring enabled.";

  const getRelationshipBadge = (relationship) => {
    const rel = String(relationship || '').toUpperCase();
    switch (rel) {
      case 'CONTRADICTS':
        return {
          icon: <AlertTriangle size={15} color="#f43f5e" />,
          label: 'CONTRADICTS CLAIM',
          bgColor: 'rgba(244, 63, 94, 0.12)',
          borderColor: 'rgba(244, 63, 94, 0.4)',
          textColor: '#fb7185',
        };
      case 'REQUIRES_VERIFICATION':
        return {
          icon: <HelpCircle size={15} color="#f59e0b" />,
          label: 'REQUIRES VERIFICATION',
          bgColor: 'rgba(245, 158, 11, 0.12)',
          borderColor: 'rgba(245, 158, 11, 0.4)',
          textColor: '#fbbf24',
        };
      case 'SUPPORTS':
      default:
        return {
          icon: <CheckCircle2 size={15} color="#10b981" />,
          label: 'SUPPORTS CLAIM',
          bgColor: 'rgba(16, 185, 129, 0.12)',
          borderColor: 'rgba(16, 185, 129, 0.4)',
          textColor: '#34d399',
        };
    }
  };

  const getDimensionIcon = (dim) => {
    const d = String(dim || '').toLowerCase();
    if (d.includes('1') || d.includes('inventory')) {
      return <ShoppingBag size={18} color="#60a5fa" />;
    }
    if (d.includes('2') || d.includes('brand') || d.includes('logo')) {
      return <Award size={18} color="#c084fc" />;
    }
    return <FileCheck2 size={18} color="#34d399" />;
  };

  return (
    <div style={{ marginBottom: '2.5rem' }}>
      <div style={{ marginBottom: '1.25rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div>
          <h3 style={{ fontSize: '1.3rem', fontWeight: 800, color: '#ffffff', display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <Scale size={22} color="#3b82f6" />
            Claim ↔ Visual Evidence Reasoning Layer
          </h3>
          <p style={{ fontSize: '0.86rem', color: '#94a3b8', marginTop: '0.2rem' }}>
            Core question: <em>«Does the visual evidence associated with this merchant support or contradict what they claim?»</em>
          </p>
        </div>
        <span className="status-pill purple">
          <Sparkles size={13} />
          <span>SYNTHESIZED REASONING</span>
        </span>
      </div>

      {/* Side-by-Side Matrix Grid */}
      {claimItems.length > 0 && (
        <div className="grid-3" style={{ gap: '1.25rem' }}>
          {claimItems.map((item, idx) => {
            const badge = getRelationshipBadge(item?.relationship);
            const isOnline = item?.source_type === 'ONLINE';

            return (
              <div
                key={idx}
                className="card"
                style={{
                  padding: '1.25rem',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                }}
              >
                <div>
                  <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#ffffff', display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.85rem' }}>
                    {getDimensionIcon(item?.dimension)}
                    <span>{item?.dimension || `Evidence Dimension #${idx + 1}`}</span>
                  </h4>

                  {/* Merchant Claim Box */}
                  <div
                    style={{
                      background: '#0d0e14',
                      border: '1px solid #23242e',
                      borderRadius: '8px',
                      padding: '0.75rem',
                      marginBottom: '0.85rem',
                    }}
                  >
                    <div style={{ fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '0.06em', color: '#64748b', fontWeight: 700, marginBottom: '0.25rem' }}>
                      MERCHANT STATED CLAIM
                    </div>
                    <div style={{ fontSize: '0.85rem', color: '#e2e8f0', fontStyle: 'italic', lineHeight: 1.4 }}>
                      "{item?.claim || 'Standard business merchant registration.'}"
                    </div>
                  </div>

                  {/* Visual Evidence Finding Box */}
                  <div
                    style={{
                      background: badge.bgColor,
                      border: `1px solid ${badge.borderColor}`,
                      borderRadius: '8px',
                      padding: '0.85rem',
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
                          fontWeight: 800,
                          fontSize: '0.75rem',
                          color: badge.textColor,
                          letterSpacing: '0.04em',
                        }}
                      >
                        {badge.icon}
                        <span>{badge.label}</span>
                      </div>

                      <span
                        style={{
                          fontSize: '0.68rem',
                          fontWeight: 700,
                          padding: '0.15rem 0.45rem',
                          borderRadius: '4px',
                          background: isOnline ? 'rgba(59, 130, 246, 0.2)' : 'rgba(100, 116, 139, 0.2)',
                          color: isOnline ? '#93c5fd' : '#cbd5e1',
                          border: `1px solid ${isOnline ? 'rgba(59, 130, 246, 0.4)' : '#475569'}`,
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.25rem',
                        }}
                      >
                        {isOnline ? <Globe size={10} /> : <Database size={10} />}
                        {isOnline ? 'ONLINE EVIDENCE' : 'LOCAL CATALOG'}
                      </span>
                    </div>

                    <div style={{ fontSize: '0.83rem', color: '#f8fafc', lineHeight: 1.45 }}>
                      {item?.evidence_summary || 'Visual signals evaluated.'}
                    </div>

                    <div style={{ marginTop: '0.65rem', fontSize: '0.75rem', color: '#94a3b8', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span className="data-chip" style={{ fontSize: '0.72rem' }}>{item?.score_label || 'Empirical Match'}</span>
                      {item?.source_domain && (
                        <span style={{ fontStyle: 'italic', fontSize: '0.72rem', color: '#60a5fa' }}>
                          Source: {item.source_domain}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Dynamic Conclusion & Recommendation Synthesis Banner */}
      <div
        className="card"
        style={{
          marginTop: '1.25rem',
          padding: '1.5rem',
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: '1.5rem',
          alignItems: 'center',
          background: 'linear-gradient(135deg, rgba(18, 19, 25, 0.95) 0%, rgba(28, 30, 42, 0.9) 100%)',
          border: '1px solid rgba(59, 130, 246, 0.3)',
        }}
      >
        <div>
          <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.06em', color: '#60a5fa', fontWeight: 800, marginBottom: '0.4rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <Sparkles size={14} />
            <span>SYNTHESIZED ANALYST DOSSIER</span>
          </div>
          <div style={{ fontSize: '1.05rem', fontWeight: 600, color: '#ffffff', lineHeight: 1.45 }}>
            "{conclusion}"
          </div>
        </div>

        <div
          style={{
            borderLeft: '1px solid #23242e',
            paddingLeft: '1.5rem',
          }}
        >
          <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.06em', color: '#34d399', fontWeight: 800, marginBottom: '0.4rem' }}>
            POLICY ACTION RECOMMENDATION
          </div>
          <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#38bdf8', marginBottom: '0.75rem' }}>
            {recommendation}
          </div>

          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            <span className="status-pill emerald" style={{ fontSize: '0.72rem', padding: '0.25rem 0.65rem' }}>
              <Check size={11} /> Approve Standard Flow
            </span>
            <span className="status-pill blue" style={{ fontSize: '0.72rem', padding: '0.25rem 0.65rem' }}>
              <ArrowRight size={11} /> Request Invoice Verification
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
