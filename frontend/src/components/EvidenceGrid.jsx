import React from 'react';

export default function EvidenceGrid({ reuse, logo, manipulation, identity }) {
  const hasReuse = reuse?.max_similarity !== null && reuse?.max_similarity !== undefined;
  const hasLogo = logo?.inconsistency_risk !== null && logo?.inconsistency_risk !== undefined;
  const hasManip = manipulation?.manipulation_score !== null && manipulation?.manipulation_score !== undefined;
  const hasCoherence = identity?.coherence_score !== null && identity?.coherence_score !== undefined;

  const reusePct = hasReuse ? Math.round((reuse.max_similarity ?? 0.0) * 100) : null;
  const logoInconPct = hasLogo ? Math.round(logo.inconsistency_risk ?? 0.0) : null;
  const manipPct = hasManip ? Math.round(manipulation.manipulation_score ?? 0.0) : null;
  const coherencePct = hasCoherence ? Math.round((identity.coherence_score <= 1.0 ? identity.coherence_score * 100 : identity.coherence_score)) : null;

  const getMetricColor = (val, isCoherence = false) => {
    if (val === null || val === undefined) return 'var(--muted)';
    if (isCoherence) {
      if (val >= 75) return 'var(--risk-green)';
      if (val >= 50) return 'var(--amber)';
      return 'var(--risk-red)';
    }
    if (val >= 70) return 'var(--risk-red)';
    if (val >= 40) return 'var(--amber)';
    return 'var(--risk-green)';
  };

  return (
    <div className="metrics-grid" style={{ marginBottom: '1.5rem' }}>
      {/* Metric 1: Image Reuse */}
      <div className="metric-card">
        <span className="eyebrow">IMAGE REUSE INDEX</span>
        <div className="metric-value" style={{ color: getMetricColor(reusePct) }}>
          {reusePct !== null ? `${reusePct}%` : 'N/A'}
        </div>
        <div className="progress-track">
          <div
            className="progress-fill"
            style={{
              width: `${reusePct || 0}%`,
              background: getMetricColor(reusePct),
            }}
          />
        </div>
        <div className="metric-desc">Max ViT similarity vs web/catalog candidates</div>
      </div>

      {/* Metric 2: Logo Inconsistency */}
      <div className="metric-card">
        <span className="eyebrow">LOGO INCONSISTENCY</span>
        <div className="metric-value" style={{ color: getMetricColor(logoInconPct) }}>
          {logoInconPct !== null ? `${logoInconPct}%` : 'N/A'}
        </div>
        <div className="progress-track">
          <div
            className="progress-fill"
            style={{
              width: `${logoInconPct || 0}%`,
              background: getMetricColor(logoInconPct),
            }}
          />
        </div>
        <div className="metric-desc">Variance against verified brand marks</div>
      </div>

      {/* Metric 3: Manipulation ELA */}
      <div className="metric-card">
        <span className="eyebrow">MANIPULATION ELA</span>
        <div className="metric-value" style={{ color: getMetricColor(manipPct) }}>
          {manipPct !== null ? `${manipPct}%` : 'N/A'}
        </div>
        <div className="progress-track">
          <div
            className="progress-fill"
            style={{
              width: `${manipPct || 0}%`,
              background: getMetricColor(manipPct),
            }}
          />
        </div>
        <div className="metric-desc">Compression & gradient frequency anomalies</div>
      </div>

      {/* Metric 4: Identity Consistency */}
      <div className="metric-card">
        <span className="eyebrow">IDENTITY COHERENCE</span>
        <div className="metric-value" style={{ color: getMetricColor(coherencePct, true) }}>
          {coherencePct !== null ? `${coherencePct}%` : 'N/A'}
        </div>
        <div className="progress-track">
          <div
            className="progress-fill"
            style={{
              width: `${coherencePct || 0}%`,
              background: getMetricColor(coherencePct, true),
            }}
          />
        </div>
        <div className="metric-desc">Cross-product visual style consistency</div>
      </div>
    </div>
  );
}
