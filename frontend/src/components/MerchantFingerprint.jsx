import React from 'react';

/**
 * MerchantFingerprint — Visual Merchant Profile card.
 * All values derived from actual pipeline outputs. Shows N/A when unavailable.
 */
export default function MerchantFingerprint({ reuse, logo, manipulation, identity, fusion }) {
  if (!fusion) return null;

  // Image Consistency = inverse of max similarity variance across products
  const coherenceRaw = identity?.coherence_score ?? null;
  const coherencePct = coherenceRaw !== null
    ? (coherenceRaw <= 1.0 ? Math.round(coherenceRaw * 100) : Math.round(coherenceRaw))
    : null;

  // Visual Originality = 100 - max_similarity (how original vs known web catalog)
  const maxSim = reuse?.max_similarity ?? null;
  const originalityPct = maxSim !== null ? Math.max(0, Math.round((1.0 - maxSim) * 100)) : null;

  // Logo consistency = inverse of inconsistency_risk
  const logoRisk = logo?.inconsistency_risk ?? null;
  const logoConsistencyPct = logoRisk !== null ? Math.max(0, Math.round(100 - logoRisk)) : null;

  // External Reuse Exposure = reuse_risk_score (already 0-100)
  const reuseExposure = reuse?.reuse_risk_score != null ? Math.round(reuse.reuse_risk_score) : null;

  // Manipulation Indicators = manipulation_score (already 0-100)
  const manipScore = manipulation?.manipulation_score != null ? Math.round(manipulation.manipulation_score) : null;

  // Evidence Confidence = from fusion (computed across all vectors)
  const evidenceConf = (() => {
    const s = fusion.final_risk_score;
    if (s === null || s === undefined) return null;
    // Confidence reflects how decisive the evidence is, not how risky it is
    // Strong CLEAR = high confidence. Medium = moderate. UNVERIFIABLE = 0
    if (fusion.is_unverifiable) return 0;
    const tier = fusion.status_tier || '';
    if (tier === 'HIGH' || tier === 'CLEAR') return 90;
    if (tier === 'MEDIUM') return 72;
    if (tier === 'LOW') return 60;
    return 55;
  })();

  const metrics = [
    {
      label: 'Image Consistency',
      value: coherencePct,
      desc: 'Cross-product visual style uniformity',
      goodHigh: true,
    },
    {
      label: 'Visual Originality',
      value: originalityPct,
      desc: 'Inverse of max web catalog similarity',
      goodHigh: true,
    },
    {
      label: 'Logo Consistency',
      value: logoConsistencyPct,
      desc: 'Verified brand mark alignment',
      goodHigh: true,
    },
    {
      label: 'External Reuse Exposure',
      value: reuseExposure,
      desc: 'Image reuse risk score (0 = clean)',
      goodHigh: false,
    },
    {
      label: 'Manipulation Indicators',
      value: manipScore,
      desc: 'ELA forensic anomaly score (0 = clean)',
      goodHigh: false,
    },
    {
      label: 'Evidence Confidence',
      value: evidenceConf,
      desc: 'Decisiveness of available evidence',
      goodHigh: true,
    },
  ];

  const getBarColor = (val, goodHigh) => {
    if (val === null) return 'var(--muted)';
    if (goodHigh) {
      if (val >= 75) return 'var(--risk-green)';
      if (val >= 45) return 'var(--amber)';
      return 'var(--risk-red)';
    } else {
      if (val <= 15) return 'var(--risk-green)';
      if (val <= 50) return 'var(--amber)';
      return 'var(--risk-red)';
    }
  };

  const getTextColor = (val, goodHigh) => {
    if (val === null) return 'var(--muted)';
    return getBarColor(val, goodHigh);
  };

  return (
    <div className="card" style={{ padding: '1.25rem', marginBottom: '1.5rem' }}>
      <span className="eyebrow">VISUAL MERCHANT PROFILE</span>
      <p style={{ fontSize: '12px', color: 'var(--muted)', marginTop: '0.2rem', marginBottom: '1rem', lineHeight: 1.4 }}>
        All values derived from actual pipeline outputs. Unavailable signals shown as N/A.
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.85rem' }}>
        {metrics.map((m) => (
          <div key={m.label}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '0.2rem' }}>
              <span style={{ color: 'var(--cream)', fontWeight: 500 }}>{m.label}</span>
              <span className="font-mono" style={{ color: getTextColor(m.value, m.goodHigh), fontWeight: 700 }}>
                {m.value !== null ? `${m.value}%` : 'N/A'}
              </span>
            </div>
            <div className="progress-track" style={{ height: '4px' }}>
              <div
                className="progress-fill"
                style={{
                  width: m.value !== null ? `${m.value}%` : '0%',
                  background: getBarColor(m.value, m.goodHigh),
                  height: '4px',
                  transition: 'width 0.8s ease',
                }}
              />
            </div>
            <div style={{ fontSize: '10px', color: 'var(--muted)', marginTop: '0.2rem' }}>{m.desc}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
