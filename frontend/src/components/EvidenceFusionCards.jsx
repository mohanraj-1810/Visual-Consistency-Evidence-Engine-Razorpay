import React from 'react';
import { Layers, Globe, Database, CheckCircle2, AlertTriangle, ShieldCheck, ShieldAlert, ExternalLink, Hash } from 'lucide-react';

export default function EvidenceFusionCards({ evidence = [] }) {
  if (!evidence || evidence.length === 0) return null;

  const getScoreColor = (val) => {
    if (val >= 70) return '#ef4444';
    if (val >= 40) return '#f59e0b';
    return '#10b981';
  };

  const getEvidenceLevelBadge = (level, corroborated) => {
    if (corroborated || level === 'CORROBORATED_POTENTIAL_REUSE') {
      return {
        label: 'Corroborated Potential Visual Reuse Evidence',
        bg: 'rgba(239, 68, 68, 0.2)',
        border: '#ef4444',
        text: '#fca5a5',
        icon: <ShieldAlert size={14} color="#ef4444" />,
      };
    }
    if (level === 'POTENTIAL_REUSE') {
      return {
        label: 'Potential Visual Reuse Evidence',
        bg: 'rgba(245, 158, 11, 0.2)',
        border: '#f59e0b',
        text: '#fcd34d',
        icon: <AlertTriangle size={14} color="#f59e0b" />,
      };
    }
    return {
      label: 'Unique Visual Asset',
      bg: 'rgba(16, 185, 129, 0.2)',
      border: '#10b981',
      text: '#6ee7b7',
      icon: <ShieldCheck size={14} color="#10b981" />,
    };
  };

  return (
    <div style={{ marginBottom: '2.5rem' }}>
      <div style={{ marginBottom: '1.25rem' }}>
        <h3 style={{ fontSize: '1.3rem', fontWeight: 800, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Layers size={22} color="#6366f1" />
          Evidence Fusion Layer (Google Cloud Vision ↔ Local Platform ViT)
        </h3>
        <p style={{ fontSize: '0.86rem', color: '#94a3b8', marginTop: '0.2rem' }}>
          Cross-references each extracted asset simultaneously across open-web indexes and previous merchant visual history.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '1.25rem' }}>
        {evidence.map((item, idx) => {
          const webScore = item.google_web_match_score ?? 0;
          const vitScore = item.local_vit_similarity_score ?? 0;
          const corroborated = item.corroborated ?? false;
          const badge = getEvidenceLevelBadge(item.asset_evidence_level, corroborated);
          const matchedDomains = item.matched_domains || [];
          const maskedMerchants = item.masked_merchant_ids || [];

          return (
            <div
              key={idx}
              style={{
                background: 'linear-gradient(145deg, #1e293b 0%, #0f172a 100%)',
                border: `1px solid ${corroborated ? 'rgba(239, 68, 68, 0.4)' : '#334155'}`,
                borderRadius: '12px',
                padding: '1.25rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '1rem',
                boxShadow: corroborated ? '0 0 15px rgba(239, 68, 68, 0.15)' : 'none',
              }}
            >
              {/* Card Header: Asset Type & Badge */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.5rem', flexWrap: 'wrap' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <span
                    style={{
                      textTransform: 'uppercase',
                      fontSize: '0.72rem',
                      fontWeight: 700,
                      background: 'rgba(99, 102, 241, 0.2)',
                      color: '#a5b4fc',
                      padding: '0.2rem 0.5rem',
                      borderRadius: '4px',
                      border: '1px solid rgba(99, 102, 241, 0.3)',
                    }}
                  >
                    Asset #{idx + 1} • {item.asset_type || 'product_image'}
                  </span>
                </div>

                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.3rem',
                    background: badge.bg,
                    border: `1px solid ${badge.border}`,
                    color: badge.text,
                    padding: '0.2rem 0.6rem',
                    borderRadius: '6px',
                    fontSize: '0.75rem',
                    fontWeight: 700,
                  }}
                >
                  {badge.icon}
                  {badge.label}
                </div>
              </div>

              {/* Asset URL / Preview Hint */}
              {item.asset_url && (
                <div style={{ fontSize: '0.76rem', color: '#94a3b8', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  <strong>Source:</strong> {item.asset_url}
                </div>
              )}

              {/* Two-Source Score Comparison Bars */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', background: 'rgba(15, 23, 42, 0.6)', padding: '0.85rem', borderRadius: '8px' }}>
                {/* Source 1: Google Vision */}
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.3rem' }}>
                    <span style={{ fontSize: '0.75rem', color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                      <Globe size={13} color="#60a5fa" /> Open Web
                    </span>
                    <span style={{ fontSize: '0.82rem', fontWeight: 800, color: getScoreColor(webScore) }}>
                      {webScore}%
                    </span>
                  </div>
                  <div style={{ background: '#334155', height: '6px', borderRadius: '3px', overflow: 'hidden' }}>
                    <div style={{ width: `${Math.min(100, webScore)}%`, height: '100%', background: getScoreColor(webScore), transition: 'width 0.4s' }} />
                  </div>
                  <div style={{ fontSize: '0.68rem', color: '#64748b', marginTop: '0.3rem' }}>
                    {item.google_vision_provider_result || 'none'}
                  </div>
                </div>

                {/* Source 2: Local Platform ViT */}
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.3rem' }}>
                    <span style={{ fontSize: '0.75rem', color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                      <Database size={13} color="#a855f7" /> Platform ViT
                    </span>
                    <span style={{ fontSize: '0.82rem', fontWeight: 800, color: getScoreColor(vitScore) }}>
                      {vitScore}%
                    </span>
                  </div>
                  <div style={{ background: '#334155', height: '6px', borderRadius: '3px', overflow: 'hidden' }}>
                    <div style={{ width: `${Math.min(100, vitScore)}%`, height: '100%', background: getScoreColor(vitScore), transition: 'width 0.4s' }} />
                  </div>
                  <div style={{ fontSize: '0.68rem', color: '#64748b', marginTop: '0.3rem' }}>
                    cosine sim: {item.vit_cosine_similarity ?? 0.0}
                  </div>
                </div>
              </div>

              {/* Matched Domains & Matched Merchants Details */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', fontSize: '0.78rem' }}>
                {matchedDomains.length > 0 && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', flexWrap: 'wrap' }}>
                    <strong style={{ color: '#cbd5e1' }}>Matched Web Domains:</strong>
                    {matchedDomains.map((d, i) => (
                      <span key={i} style={{ background: 'rgba(59, 130, 246, 0.15)', color: '#93c5fd', padding: '0.1rem 0.4rem', borderRadius: '4px', border: '1px solid rgba(59, 130, 246, 0.3)' }}>
                        {d}
                      </span>
                    ))}
                  </div>
                )}

                {maskedMerchants.length > 0 && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', flexWrap: 'wrap' }}>
                    <strong style={{ color: '#cbd5e1' }}>Matched Platform Merchants:</strong>
                    {maskedMerchants.map((m, i) => (
                      <span key={i} style={{ background: 'rgba(168, 85, 247, 0.15)', color: '#d8b4fe', padding: '0.1rem 0.4rem', borderRadius: '4px', border: '1px solid rgba(168, 85, 247, 0.3)' }}>
                        {m}
                      </span>
                    ))}
                    <span style={{ fontSize: '0.7rem', color: '#94a3b8' }}>({maskedMerchants.length} match{maskedMerchants.length > 1 ? 'es' : ''})</span>
                  </div>
                )}
              </div>

              {/* Analyst-Safe Explanation Banner */}
              <div
                style={{
                  background: 'rgba(30, 41, 59, 0.7)',
                  borderLeft: `3px solid ${corroborated ? '#ef4444' : '#6366f1'}`,
                  padding: '0.65rem 0.85rem',
                  borderRadius: '4px',
                  fontSize: '0.8rem',
                  color: '#e2e8f0',
                  lineHeight: '1.4',
                }}
              >
                {item.explanation}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
