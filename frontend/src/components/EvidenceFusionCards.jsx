import React from 'react';
import { Layers, Globe, Database, CheckCircle2, AlertTriangle, ShieldCheck, ShieldAlert, ExternalLink, Hash, Eye, Sparkles } from 'lucide-react';

export default function EvidenceFusionCards({ evidence = [] }) {
  if (!Array.isArray(evidence) || evidence.length === 0) return null;

  const getScoreColor = (val) => {
    if (val >= 70) return '#f43f5e';
    if (val >= 40) return '#f59e0b';
    return '#10b981';
  };

  const getEvidenceLevelBadge = (level, corroborated) => {
    const lvl = String(level || '').toUpperCase();
    if (corroborated || lvl.includes('CORROBORATED') || lvl === 'HIGH') {
      return {
        label: 'Corroborated Potential Visual Reuse Evidence',
        bg: 'rgba(244, 63, 94, 0.15)',
        border: 'rgba(244, 63, 94, 0.4)',
        text: '#fb7185',
        icon: <ShieldAlert size={14} color="#f43f5e" />,
      };
    }
    if (lvl.includes('REUSE') || lvl === 'MEDIUM' || lvl === 'POTENTIAL_REUSE') {
      return {
        label: 'Potential Visual Reuse Evidence',
        bg: 'rgba(245, 158, 11, 0.15)',
        border: 'rgba(245, 158, 11, 0.4)',
        text: '#fbbf24',
        icon: <AlertTriangle size={14} color="#f59e0b" />,
      };
    }
    return {
      label: 'Unique Visual Asset',
      bg: 'rgba(16, 185, 129, 0.15)',
      border: 'rgba(16, 185, 129, 0.4)',
      text: '#34d399',
      icon: <ShieldCheck size={14} color="#10b981" />,
    };
  };

  return (
    <div style={{ marginBottom: '2.5rem' }}>
      <div style={{ marginBottom: '1.25rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div>
          <h3 style={{ fontSize: '1.3rem', fontWeight: 800, color: '#ffffff', display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <Layers size={22} color="#3b82f6" />
            Evidence Fusion Layer (Public Web ↔ Local ViT)
          </h3>
          <p style={{ fontSize: '0.86rem', color: '#94a3b8', marginTop: '0.2rem' }}>
            Cross-references each extracted asset across public web discovery sources and platform ViT embeddings.
          </p>
        </div>
        <span className="status-pill blue">
          <Eye size={13} />
          <span>DUAL-SOURCE CORROBORATION</span>
        </span>
      </div>

      <div className="grid-2" style={{ gap: '1.25rem' }}>
        {evidence.map((item, idx) => {
          if (!item || typeof item !== 'object') return null;

          const webScore = item.google_web_match_score ?? item.web_match_score ?? 0;
          const vitScore = item.local_vit_similarity_score ?? Math.round((item.vit_cosine_similarity ?? item.similarity ?? 0) * 100);
          const corroborated = Boolean(item.corroborated);
          const badge = getEvidenceLevelBadge(item.asset_evidence_level || item.level || item.risk_level, corroborated);
          const matchedDomains = Array.isArray(item.matched_domains) ? item.matched_domains : item.source_domain ? [item.source_domain] : [];
          const maskedMerchants = Array.isArray(item.masked_merchant_ids) ? item.masked_merchant_ids : [];

          return (
            <div
              key={idx}
              className="card"
              style={{
                border: `1px solid ${corroborated ? 'rgba(244, 63, 94, 0.4)' : '#23242e'}`,
                padding: '1.35rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '1rem',
                boxShadow: corroborated ? '0 0 20px rgba(244, 63, 94, 0.18)' : 'var(--shadow-card)',
              }}
            >
              {/* Card Header: Asset Type & Badge */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                <span className="data-chip highlight">
                  Asset #{idx + 1} • {item.asset_type || 'product_image'}
                </span>

                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.35rem',
                    background: badge.bg,
                    border: `1px solid ${badge.border}`,
                    color: badge.text,
                    padding: '0.25rem 0.65rem',
                    borderRadius: '6px',
                    fontSize: '0.75rem',
                    fontWeight: 700,
                  }}
                >
                  {badge.icon}
                  <span>{badge.label}</span>
                </div>
              </div>

              {/* Asset URL */}
              {item.asset_url && (
                <div style={{ fontSize: '0.76rem', color: '#94a3b8', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  <strong style={{ color: '#cbd5e1' }}>Asset URL:</strong> {String(item.asset_url)}
                </div>
              )}

              {/* Two-Source Score Comparison Bars */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr',
                  gap: '1rem',
                  background: '#0d0e14',
                  border: '1px solid #23242e',
                  padding: '1rem',
                  borderRadius: '8px',
                }}
              >
                {/* Source 1: Web Match */}
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                    <span style={{ fontSize: '0.75rem', color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                      <Globe size={13} color="#60a5fa" /> Web Search Match
                    </span>
                    <span style={{ fontSize: '0.85rem', fontWeight: 800, color: getScoreColor(webScore), fontFamily: 'JetBrains Mono' }}>
                      {webScore}%
                    </span>
                  </div>
                  <div style={{ background: '#1c1e28', height: '6px', borderRadius: '3px', overflow: 'hidden' }}>
                    <div style={{ width: `${Math.min(100, Math.max(0, webScore))}%`, height: '100%', background: getScoreColor(webScore), transition: 'width 0.4s' }} />
                  </div>
                  <div style={{ fontSize: '0.7rem', color: '#64748b', marginTop: '0.35rem', textTransform: 'capitalize' }}>
                    {item.provider_result ? String(item.provider_result).replace('_', ' ') : 'web discovery'}
                  </div>
                </div>

                {/* Source 2: Local Platform ViT */}
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                    <span style={{ fontSize: '0.75rem', color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                      <Database size={13} color="#c084fc" /> Platform ViT
                    </span>
                    <span style={{ fontSize: '0.85rem', fontWeight: 800, color: getScoreColor(vitScore), fontFamily: 'JetBrains Mono' }}>
                      {vitScore}%
                    </span>
                  </div>
                  <div style={{ background: '#1c1e28', height: '6px', borderRadius: '3px', overflow: 'hidden' }}>
                    <div style={{ width: `${Math.min(100, Math.max(0, vitScore))}%`, height: '100%', background: getScoreColor(vitScore), transition: 'width 0.4s' }} />
                  </div>
                  <div style={{ fontSize: '0.7rem', color: '#64748b', marginTop: '0.35rem' }}>
                    cosine sim: <span style={{ fontFamily: 'JetBrains Mono', color: '#cbd5e1' }}>{item.vit_cosine_similarity ?? (vitScore / 100).toFixed(2)}</span>
                  </div>
                </div>
              </div>

              {/* Matched Domains & Matched Merchants Details */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', fontSize: '0.78rem' }}>
                {matchedDomains.length > 0 && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', flexWrap: 'wrap' }}>
                    <strong style={{ color: '#cbd5e1' }}>Matched Web Domains:</strong>
                    {matchedDomains.map((d, i) => (
                      <span key={i} className="data-chip highlight" style={{ fontSize: '0.72rem', padding: '0.15rem 0.45rem' }}>
                        {String(d)}
                      </span>
                    ))}
                  </div>
                )}

                {maskedMerchants.length > 0 && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', flexWrap: 'wrap' }}>
                    <strong style={{ color: '#cbd5e1' }}>Matched Platform Merchants:</strong>
                    {maskedMerchants.map((m, i) => (
                      <span key={i} className="data-chip" style={{ fontSize: '0.72rem', padding: '0.15rem 0.45rem', borderColor: 'rgba(192, 132, 252, 0.4)', color: '#d8b4fe' }}>
                        {String(m)}
                      </span>
                    ))}
                    <span style={{ fontSize: '0.7rem', color: '#64748b' }}>({maskedMerchants.length} record{maskedMerchants.length > 1 ? 's' : ''})</span>
                  </div>
                )}
              </div>

              {/* Analyst Explanation Banner */}
              {item.explanation && (
                <div
                  style={{
                    background: 'rgba(14, 15, 20, 0.85)',
                    borderLeft: `3px solid ${corroborated ? '#f43f5e' : '#3b82f6'}`,
                    padding: '0.75rem 0.95rem',
                    borderRadius: '6px',
                    fontSize: '0.82rem',
                    color: '#e2e8f0',
                    lineHeight: '1.45',
                  }}
                >
                  {item.explanation}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
