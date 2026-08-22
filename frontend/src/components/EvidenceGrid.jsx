import React from 'react';
import { Layers, Info } from 'lucide-react';

export default function EvidenceGrid({ reuse, logo, manipulation, identity }) {
  const reusePct = Math.round((reuse?.max_similarity ?? 0.0) * 100);
  const logoInconPct = Math.round(logo?.inconsistency_risk ?? 0.0);
  const manipPct = Math.round(manipulation?.manipulation_score ?? 0.0);
  const synthPct = Math.round(manipulation?.synthetic_score ?? 0.0);
  const coherencePct = Math.round(identity?.coherence_score ?? 70.0);

  const getProgressColor = (val, thresholds = [40, 70]) => {
    if (val >= thresholds[1]) return '#ef4444';
    if (val >= thresholds[0]) return '#f59e0b';
    return '#10b981';
  };

  const getCoherenceColor = (val) => {
    if (val >= 80) return '#10b981';
    if (val >= 55) return '#f59e0b';
    return '#ef4444';
  };

  const coherenceTierLabel =
    coherencePct >= 80
      ? 'Strong internal consistency'
      : coherencePct >= 55
      ? 'Moderate internal consistency'
      : 'Low coherence (disparate origins)';

  return (
    <div style={{ marginBottom: '2.5rem' }}>
      <div style={{ marginBottom: '1rem' }}>
        <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Layers size={20} color="#6366f1" />
          Empirical Signal Breakdown
        </h3>
        <p style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
          Real-time algorithmic measurements extracted from Vision Transformer embeddings and computer vision filters.
        </p>
      </div>

      <div className="signals-grid">
        {/* Signal 1: Image Reuse */}
        <div className="signal-card">
          <div className="signal-label">Image Reuse</div>
          <div className="signal-value" style={{ color: getProgressColor(reusePct, [70, 85]) }}>
            {reusePct}%
          </div>
          <div className="progress-bar-bg">
            <div
              className="progress-bar-fill"
              style={{
                width: `${Math.min(100, reusePct)}%`,
                backgroundColor: getProgressColor(reusePct, [70, 85]),
              }}
            />
          </div>
          <div className="signal-desc">Max ViT similarity vs candidate</div>
        </div>

        {/* Signal 2: Logo Inconsistency */}
        <div className="signal-card">
          <div className="signal-label">Logo Inconsistency</div>
          <div className="signal-value" style={{ color: getProgressColor(logoInconPct, [30, 60]) }}>
            {logoInconPct}%
          </div>
          <div className="progress-bar-bg">
            <div
              className="progress-bar-fill"
              style={{
                width: `${Math.min(100, logoInconPct)}%`,
                backgroundColor: getProgressColor(logoInconPct, [30, 60]),
              }}
            />
          </div>
          <div className="signal-desc">Variance from verified identity</div>
        </div>

        {/* Signal 3: Manipulation Indicators */}
        <div className="signal-card">
          <div className="signal-label">Manipulation Indicators</div>
          <div className="signal-value" style={{ color: getProgressColor(manipPct, [35, 65]) }}>
            {manipPct}%
          </div>
          <div className="progress-bar-bg">
            <div
              className="progress-bar-fill"
              style={{
                width: `${Math.min(100, manipPct)}%`,
                backgroundColor: getProgressColor(manipPct, [35, 65]),
              }}
            />
          </div>
          <div className="signal-desc">Compression & gradient anomalies</div>
        </div>

        {/* Signal 4: Synthetic Suspicion */}
        <div className="signal-card">
          <div className="signal-label">Synthetic Suspicion (Supporting)</div>
          <div className="signal-value" style={{ color: synthPct >= 60 ? '#f59e0b' : '#60a5fa' }}>
            {synthPct}%
          </div>
          <div className="progress-bar-bg">
            <div
              className="progress-bar-fill"
              style={{
                width: `${Math.min(100, synthPct)}%`,
                backgroundColor: synthPct >= 60 ? '#f59e0b' : '#60a5fa',
              }}
            />
          </div>
          <div className="signal-desc">Supporting frequency signal only</div>
        </div>

        {/* Signal 5: Identity Consistency */}
        <div className="signal-card">
          <div className="signal-label">Identity Consistency</div>
          <div className="signal-value" style={{ color: getCoherenceColor(coherencePct) }}>
            {coherencePct}%
          </div>
          <div className="progress-bar-bg">
            <div
              className="progress-bar-fill"
              style={{
                width: `${Math.min(100, coherencePct)}%`,
                backgroundColor: getCoherenceColor(coherencePct),
              }}
            />
          </div>
          <div className="signal-desc">{coherenceTierLabel}</div>
        </div>
      </div>
    </div>
  );
}
