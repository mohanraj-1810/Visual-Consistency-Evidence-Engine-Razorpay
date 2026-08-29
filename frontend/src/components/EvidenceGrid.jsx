import React from 'react';
import { Layers, Activity, ShieldCheck, Image as ImageIcon, Eye, Sparkles } from 'lucide-react';

export default function EvidenceGrid({ reuse, logo, manipulation, identity }) {
  const hasReuse = reuse?.max_similarity !== null && reuse?.max_similarity !== undefined;
  const hasLogo = logo?.inconsistency_risk !== null && logo?.inconsistency_risk !== undefined;
  const hasManip = manipulation?.manipulation_score !== null && manipulation?.manipulation_score !== undefined;
  const hasCoherence = identity?.coherence_score !== null && identity?.coherence_score !== undefined;

  const reusePct = hasReuse ? Math.round((reuse.max_similarity ?? 0.0) * 100) : null;
  const logoInconPct = hasLogo ? Math.round(logo.inconsistency_risk ?? 0.0) : null;
  const manipPct = hasManip ? Math.round(manipulation.manipulation_score ?? 0.0) : null;
  const coherencePct = hasCoherence ? Math.round((identity.coherence_score <= 1.0 ? identity.coherence_score * 100 : identity.coherence_score)) : null;

  const getProgressColor = (val, thresholds = [40, 70]) => {
    if (val === null || val === undefined) return '#64748b';
    if (val >= thresholds[1]) return '#f43f5e';
    if (val >= thresholds[0]) return '#f59e0b';
    return '#10b981';
  };

  const getCoherenceColor = (val) => {
    if (val === null || val === undefined) return '#64748b';
    if (val >= 80) return '#10b981';
    if (val >= 55) return '#f59e0b';
    return '#f43f5e';
  };

  const coherenceTierLabel =
    coherencePct === null
      ? 'No visual assets to measure'
      : coherencePct >= 80
      ? 'Strong internal visual consistency'
      : coherencePct >= 55
      ? 'Moderate internal visual consistency'
      : 'Low coherence (disparate origins)';

  return (
    <div style={{ marginBottom: '2.5rem' }}>
      <div style={{ marginBottom: '1.25rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div>
          <h3 style={{ fontSize: '1.3rem', fontWeight: 800, color: '#ffffff', display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <Layers size={22} color="#3b82f6" />
            Empirical Visual Signal Breakdown
          </h3>
          <p style={{ fontSize: '0.86rem', color: '#94a3b8', marginTop: '0.2rem' }}>
            Real-time algorithmic measurements extracted from Vision Transformer embeddings and computer vision filters.
          </p>
        </div>
        <span className="status-pill purple">
          <Activity size={13} />
          <span>FORENSIC METRICS</span>
        </span>
      </div>

      <div className="grid-4" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1.25rem' }}>
        {/* Signal 1: Image Reuse */}
        <div className="card" style={{ padding: '1.25rem' }}>
          <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.06em', color: '#94a3b8', fontWeight: 700, marginBottom: '0.4rem' }}>
            Image Reuse Index
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: getProgressColor(reusePct, [70, 85]), fontFamily: 'JetBrains Mono' }}>
            {reusePct !== null ? `${reusePct}%` : 'N/A'}
          </div>
          <div style={{ background: '#0d0e14', height: '6px', borderRadius: '3px', margin: '0.6rem 0', overflow: 'hidden', border: '1px solid #23242e' }}>
            <div
              style={{
                width: reusePct !== null ? `${Math.min(100, reusePct)}%` : '0%',
                height: '100%',
                backgroundColor: getProgressColor(reusePct, [70, 85]),
                transition: 'width 0.4s ease',
              }}
            />
          </div>
          <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Max ViT similarity vs candidate</div>
        </div>

        {/* Signal 2: Logo Inconsistency */}
        <div className="card" style={{ padding: '1.25rem' }}>
          <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.06em', color: '#94a3b8', fontWeight: 700, marginBottom: '0.4rem' }}>
            Logo Inconsistency
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: getProgressColor(logoInconPct, [30, 60]), fontFamily: 'JetBrains Mono' }}>
            {logoInconPct !== null ? `${logoInconPct}%` : 'N/A'}
          </div>
          <div style={{ background: '#0d0e14', height: '6px', borderRadius: '3px', margin: '0.6rem 0', overflow: 'hidden', border: '1px solid #23242e' }}>
            <div
              style={{
                width: logoInconPct !== null ? `${Math.min(100, logoInconPct)}%` : '0%',
                height: '100%',
                backgroundColor: getProgressColor(logoInconPct, [30, 60]),
                transition: 'width 0.4s ease',
              }}
            />
          </div>
          <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Variance from verified identity</div>
        </div>

        {/* Signal 3: Manipulation Indicators */}
        <div className="card" style={{ padding: '1.25rem' }}>
          <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.06em', color: '#94a3b8', fontWeight: 700, marginBottom: '0.4rem' }}>
            Manipulation ELA
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: getProgressColor(manipPct, [35, 65]), fontFamily: 'JetBrains Mono' }}>
            {manipPct !== null ? `${manipPct}%` : 'N/A'}
          </div>
          <div style={{ background: '#0d0e14', height: '6px', borderRadius: '3px', margin: '0.6rem 0', overflow: 'hidden', border: '1px solid #23242e' }}>
            <div
              style={{
                width: manipPct !== null ? `${Math.min(100, manipPct)}%` : '0%',
                height: '100%',
                backgroundColor: getProgressColor(manipPct, [35, 65]),
                transition: 'width 0.4s ease',
              }}
            />
          </div>
          <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Compression & gradient anomalies</div>
        </div>

        {/* Signal 4: Identity Consistency */}
        <div className="card" style={{ padding: '1.25rem' }}>
          <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.06em', color: '#94a3b8', fontWeight: 700, marginBottom: '0.4rem' }}>
            Identity Consistency
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: getCoherenceColor(coherencePct), fontFamily: 'JetBrains Mono' }}>
            {coherencePct !== null ? `${coherencePct}%` : 'N/A'}
          </div>
          <div style={{ background: '#0d0e14', height: '6px', borderRadius: '3px', margin: '0.6rem 0', overflow: 'hidden', border: '1px solid #23242e' }}>
            <div
              style={{
                width: coherencePct !== null ? `${Math.min(100, coherencePct)}%` : '0%',
                height: '100%',
                backgroundColor: getCoherenceColor(coherencePct),
                transition: 'width 0.4s ease',
              }}
            />
          </div>
          <div style={{ fontSize: '0.75rem', color: '#64748b' }}>{coherenceTierLabel}</div>
        </div>
      </div>
    </div>
  );
}
