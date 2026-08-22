import React, { useState } from 'react';
import {
  Search,
  Eye,
  Scale,
  Download,
  FileText,
  CheckCircle2,
  AlertTriangle,
  ShieldAlert,
  ExternalLink,
  Globe,
  Database,
  Cpu,
  Layers,
  HelpCircle,
} from 'lucide-react';

export default function HeatmapViewer({ result }) {
  const [activeTab, setActiveTab] = useState('reuse'); // 'reuse' | 'forensics' | 'audit' | 'provenance' | 'json'

  if (!result) return null;

  const {
    fusion,
    visual_risk,
    text_risk,
    reuse,
    identity,
    logo,
    manipulation,
    claims,
    weights,
    structured_evidence,
    claims_reasoning,
    provenance,
    candidate_evidence,
    forensic_target_image_base64,
    ela_image_base64,
    heatmap_overlay_base64,
    product_images_base64,
    logo_image_base64,
    matched_reference_image_base64,
    matched_logo_reference_base64,
  } = result;

  const topItem = reuse?.top_flagged_item;
  const topSim = topItem?.similarity ?? 0.0;
  const topSimPct = Math.round(topSim * 100);
  const isOnline = topItem?.source_type === 'ONLINE';
  const sourceDomain = topItem?.source_domain || (isOnline ? 'public-web-source.com' : 'archive.merchant-catalog.org');
  const sourceUrl = topItem?.source_url || (topItem?.reference_path ? `https://archive.merchant-catalog.org/assets/${topItem.reference_filename}` : null);
  const refFilename = topItem?.reference_filename ?? 'candidate_match.jpg';

  const logoSimPct = Math.round((logo?.similarity ?? 1.0) * 100);
  const logoMatchedName = logo?.matched_reference ?? 'Official Identity Mark';

  const downloadJsonReport = () => {
    const exportData = {
      timestamp: new Date().toISOString(),
      merchant_name: fusion.merchant_name,
      final_risk_score: fusion.final_risk_score,
      status: fusion.status,
      status_label: fusion.status_label,
      recommendation: fusion.recommendation,
      reasons: fusion.reasons,
      claims_vs_visual_evidence: claims_reasoning,
      structured_evidence: structured_evidence,
      provenance: provenance,
      scores: {
        text_risk_score: text_risk?.text_risk_score,
        visual_risk_score: visual_risk?.visual_risk_score,
        reuse_similarity_max: reuse?.max_similarity ?? 0.0,
        identity_coherence_score: identity?.coherence_score ?? 70.0,
        logo_inconsistency: logo?.inconsistency_risk ?? 0.0,
        manipulation_score: manipulation?.manipulation_score ?? 0.0,
        synthetic_score: manipulation?.synthetic_score ?? 0.0,
      },
      weights: weights,
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `evidence_dossier_${(fusion.merchant_name || 'merchant').toLowerCase().replace(/\s+/g, '_')}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  return (
    <div className="card" style={{ padding: '1.5rem', marginBottom: '2rem' }}>
      {/* Rationale Section */}
      <div style={{ marginBottom: '1.5rem', background: '#0f172a', padding: '1.1rem 1.35rem', borderRadius: '8px', border: '1px solid #334155' }}>
        <h4 style={{ color: '#f8fafc', fontSize: '1.05rem', fontWeight: 800, marginBottom: '0.6rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          💡 Why is this merchant categorized as <span style={{ color: fusion.badge_color }}>{fusion.status} RISK</span>?
        </h4>
        <ul style={{ paddingLeft: '1.2rem', color: '#cbd5e1', fontSize: '0.88rem', lineHeight: '1.6' }}>
          {fusion.reasons?.map((r, i) => (
            <li key={i} style={{ marginBottom: '0.35rem' }}>
              <strong>{i + 1}.</strong> {r}
            </li>
          ))}
        </ul>
      </div>

      {/* Deep-Dive Navigation Tabs */}
      <div className="deepdive-tabs">
        <button
          className={`deepdive-tab-btn ${activeTab === 'reuse' ? 'active' : ''}`}
          onClick={() => setActiveTab('reuse')}
        >
          <Search size={16} />
          🔍 Candidate Visual Evidence & Logo Match
        </button>
        <button
          className={`deepdive-tab-btn ${activeTab === 'forensics' ? 'active' : ''}`}
          onClick={() => setActiveTab('forensics')}
        >
          <Eye size={16} />
          🔬 Forensic Manipulation & Heatmap
        </button>
        <button
          className={`deepdive-tab-btn ${activeTab === 'audit' ? 'active' : ''}`}
          onClick={() => setActiveTab('audit')}
        >
          <Scale size={16} />
          ⚖️ Multimodal Risk Weights & Audit
        </button>
        <button
          className={`deepdive-tab-btn ${activeTab === 'provenance' ? 'active' : ''}`}
          onClick={() => setActiveTab('provenance')}
        >
          <Cpu size={16} />
          🛠️ Technical Provenance & Model
        </button>
        <button
          className={`deepdive-tab-btn ${activeTab === 'json' ? 'active' : ''}`}
          onClick={() => setActiveTab('json')}
        >
          <FileText size={16} />
          📄 JSON Evidence Export
        </button>
      </div>

      {/* Tab 1: Image Reuse & Logo */}
      {activeTab === 'reuse' && (
        <div>
          {/* Section 1: Candidate Visual Match */}
          <div style={{ marginBottom: '2rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
              <h4 style={{ color: '#f8fafc', margin: 0 }}>1. Product Visual Verification vs. Candidate Evidence</h4>
              <span
                style={{
                  fontSize: '0.72rem',
                  fontWeight: 700,
                  padding: '0.2rem 0.6rem',
                  borderRadius: '4px',
                  background: isOnline ? 'rgba(59, 130, 246, 0.2)' : 'rgba(100, 116, 139, 0.2)',
                  color: isOnline ? '#93c5fd' : '#cbd5e1',
                  border: `1px solid ${isOnline ? '#3b82f6' : '#475569'}`,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.35rem',
                }}
              >
                {isOnline ? <Globe size={13} /> : <Database size={13} />}
                EVIDENCE SOURCE: {isOnline ? 'ONLINE WEB DISCOVERY' : 'LOCAL DEMO REFERENCE'}
              </span>
            </div>
            <p style={{ color: '#94a3b8', fontSize: '0.82rem', marginBottom: '1.25rem' }}>
              Candidate public imagery is discovered and verified using our Vision Transformer (ViT) cosine embeddings.
              Lighter similarity is labeled objectively as <em>Potential Visual Match</em>.
            </p>

            {matched_reference_image_base64 ? (
              <div className="comparison-grid">
                <div className="image-preview-box">
                  <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#94a3b8', marginBottom: '0.5rem' }}>
                    Merchant Product Visual
                  </div>
                  {product_images_base64 && product_images_base64.length > 0 ? (
                    <img src={product_images_base64[topItem?.image_index || 0]} alt="Merchant Visual" />
                  ) : (
                    <div style={{ color: '#64748b', padding: '2rem' }}>Product Visual</div>
                  )}
                </div>

                <div className="image-preview-box">
                  <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#94a3b8', marginBottom: '0.5rem' }}>
                    Potential Visual Match (<code>{refFilename}</code>)
                  </div>
                  <img src={matched_reference_image_base64} alt="Candidate Match" />
                </div>

                <div style={{ background: '#0f172a', padding: '1.25rem', borderRadius: '8px', border: '1px solid #334155' }}>
                  <span className={`evidence-tag ${topItem?.risk_level === 'HIGH' ? 'tag-red' : topItem?.risk_level === 'MEDIUM' ? 'tag-amber' : 'tag-green'}`}>
                    {topItem?.risk_level === 'HIGH' ? 'POTENTIAL VISUAL MATCH' : topItem?.risk_level === 'MEDIUM' ? 'MODERATE SIMILARITY' : 'LOW SIMILARITY'}
                  </span>

                  <div style={{ marginTop: '0.85rem', fontSize: '0.85rem', color: '#e2e8f0', lineHeight: '1.5' }}>
                    <strong>ViT Similarity Score:</strong>{' '}
                    <span style={{ fontSize: '1.1rem', fontWeight: 800, color: topSim >= 0.85 ? '#ef4444' : topSim >= 0.70 ? '#f59e0b' : '#10b981' }}>
                      {topSimPct}%
                    </span>
                  </div>

                  <div style={{ marginTop: '0.5rem', fontSize: '0.8rem', color: '#94a3b8' }}>
                    <strong>Evidence Strength:</strong> {topItem?.risk_level}
                  </div>

                  <div style={{ marginTop: '0.5rem', fontSize: '0.8rem', color: '#94a3b8' }}>
                    <strong>Source Domain:</strong> <code>{sourceDomain}</code>
                  </div>

                  {sourceUrl && (
                    <div style={{ marginTop: '0.6rem' }}>
                      <a
                        href={sourceUrl}
                        target="_blank"
                        rel="noreferrer"
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '0.3rem',
                          fontSize: '0.75rem',
                          color: '#60a5fa',
                          textDecoration: 'none',
                        }}
                      >
                        <ExternalLink size={12} />
                        Inspect Candidate Source URL
                      </a>
                    </div>
                  )}

                  <p style={{ marginTop: '0.75rem', fontSize: '0.8rem', color: '#cbd5e1' }}>
                    {topItem?.explanation}
                  </p>
                </div>
              </div>
            ) : (
              <div style={{ background: '#0f172a', padding: '1rem', borderRadius: '8px', color: '#94a3b8', fontSize: '0.85rem' }}>
                No candidate image reuse identified. Merchant imagery appears original.
              </div>
            )}
          </div>

          {/* Section 2: Logo Consistency */}
          <div style={{ borderTop: '1px solid #334155', paddingTop: '1.75rem' }}>
            <h4 style={{ color: '#f8fafc', marginBottom: '0.25rem' }}>2. Brand Identity & Logo Visual Consistency</h4>
            <p style={{ color: '#94a3b8', fontSize: '0.82rem', marginBottom: '1rem' }}>
              Compares merchant logo against verified brand assets to evaluate stylistic divergence (labeled objectively as <em>Visual Identity Inconsistency</em>).
            </p>

            {matched_logo_reference_base64 && logo_image_base64 ? (
              <div className="comparison-grid">
                <div className="image-preview-box">
                  <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#94a3b8', marginBottom: '0.5rem' }}>
                    Merchant Claimed Logo
                  </div>
                  <img src={logo_image_base64} alt="Merchant Logo" />
                </div>

                <div className="image-preview-box">
                  <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#94a3b8', marginBottom: '0.5rem' }}>
                    Verified Reference Identity (<code>{logoMatchedName}</code>)
                  </div>
                  <img src={matched_logo_reference_base64} alt="Verified Logo" />
                </div>

                <div style={{ background: '#0f172a', padding: '1.25rem', borderRadius: '8px', border: '1px solid #334155' }}>
                  <span className={`evidence-tag ${logoSimPct < 55 ? 'tag-red' : logoSimPct < 82 ? 'tag-amber' : 'tag-green'}`}>
                    {logoSimPct < 55 ? 'VISUAL IDENTITY INCONSISTENCY' : logoSimPct < 82 ? 'MODERATE VARIANCE' : 'CONSISTENT IDENTITY'}
                  </span>

                  <div style={{ marginTop: '0.85rem', fontSize: '0.85rem', color: '#e2e8f0', lineHeight: '1.5' }}>
                    <strong>Logo Alignment Score:</strong>{' '}
                    <span style={{ fontSize: '1.1rem', fontWeight: 800, color: logoSimPct < 55 ? '#ef4444' : logoSimPct < 82 ? '#f59e0b' : '#10b981' }}>
                      {logoSimPct}%
                    </span>
                  </div>

                  <div style={{ marginTop: '0.5rem', fontSize: '0.8rem', color: '#94a3b8' }}>
                    <strong>Inconsistency Risk:</strong> {Math.round(logo?.inconsistency_risk ?? 0)}%
                  </div>

                  <p style={{ marginTop: '0.75rem', fontSize: '0.8rem', color: '#cbd5e1' }}>
                    {logo?.explanation}
                  </p>
                </div>
              </div>
            ) : (
              <div style={{ background: '#0f172a', padding: '1rem', borderRadius: '8px', color: '#94a3b8', fontSize: '0.85rem' }}>
                No logo uploaded or no reference brand registered.
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 2: Forensics & Heatmap */}
      {activeTab === 'forensics' && (
        <div>
          <h4 style={{ color: '#f8fafc', marginBottom: '0.25rem' }}>Forensic Tampering & Pixel Anomaly Scan</h4>
          <p style={{ color: '#94a3b8', fontSize: '0.82rem', marginBottom: '1.25rem' }}>
            Multi-spectral Error Level Analysis (ELA) and Laplacian gradient variance to detect localized editing anomalies.
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginBottom: '1.5rem' }}>
            <div className="image-preview-box">
              <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#94a3b8', marginBottom: '0.5rem' }}>
                1. Original Visual Asset
              </div>
              {forensic_target_image_base64 ? (
                <img src={forensic_target_image_base64} alt="Original Document" />
              ) : (
                <div style={{ color: '#64748b', padding: '3rem 1rem' }}>No document provided</div>
              )}
            </div>

            <div className="image-preview-box">
              <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#94a3b8', marginBottom: '0.5rem' }}>
                2. Error Level Analysis (ELA)
              </div>
              {ela_image_base64 ? (
                <img src={ela_image_base64} alt="ELA Difference" />
              ) : (
                <div style={{ color: '#64748b', padding: '3rem 1rem' }}>ELA not computed</div>
              )}
            </div>

            <div className="image-preview-box">
              <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#94a3b8', marginBottom: '0.5rem' }}>
                3. Forensic Heatmap & Anomaly Bounding Boxes
              </div>
              {heatmap_overlay_base64 ? (
                <img src={heatmap_overlay_base64} alt="Heatmap Overlay" />
              ) : (
                <div style={{ color: '#64748b', padding: '3rem 1rem' }}>Heatmap not computed</div>
              )}
            </div>
          </div>

          <div style={{ background: '#0f172a', padding: '1.25rem', borderRadius: '8px', border: '1px solid #334155' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
              <div>
                <span className={`evidence-tag ${manipulation?.risk_level === 'HIGH' ? 'tag-red' : manipulation?.risk_level === 'MEDIUM' ? 'tag-amber' : 'tag-green'}`}>
                  {manipulation?.risk_level === 'HIGH' ? 'MANIPULATION INDICATORS DETECTED' : manipulation?.risk_level === 'MEDIUM' ? 'MODERATE ANOMALIES' : 'UNIFORM PIXEL COMPRESSION'}
                </span>
                <div style={{ marginTop: '0.5rem', fontSize: '0.85rem', color: '#e2e8f0' }}>
                  <strong>Manipulation Score:</strong> {manipulation?.manipulation_score}%
                </div>
              </div>

              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
                  Synthetic-Image Suspicion: <strong style={{ color: manipulation?.synthetic_score >= 60 ? '#f59e0b' : '#60a5fa' }}>{manipulation?.synthetic_score}%</strong>
                </div>
                <div style={{ fontSize: '0.72rem', color: '#64748b', marginTop: '0.2rem' }}>
                  Supporting signal only — not used independently for rejection.
                </div>
              </div>
            </div>

            <p style={{ marginTop: '0.75rem', fontSize: '0.8rem', color: '#cbd5e1' }}>
              {manipulation?.explanation}
            </p>
          </div>
        </div>
      )}

      {/* Tab 3: Multimodal Risk Weights & Breakdown */}
      {activeTab === 'audit' && (
        <div>
          <h4 style={{ color: '#f8fafc', marginBottom: '0.25rem' }}>Multimodal Risk Fusion & Signal Weighting</h4>
          <p style={{ color: '#94a3b8', fontSize: '0.82rem', marginBottom: '1.25rem' }}>
            Transparent breakdown of individual computer vision weights, multi-signal corroboration, and simulated text risk combination.
          </p>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem', textAlign: 'left' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #334155', color: '#94a3b8' }}>
                  <th style={{ padding: '0.75rem 0.5rem' }}>Signal Dimension</th>
                  <th style={{ padding: '0.75rem 0.5rem' }}>Raw Score</th>
                  <th style={{ padding: '0.75rem 0.5rem' }}>Weight</th>
                  <th style={{ padding: '0.75rem 0.5rem' }}>Weighted Contribution</th>
                  <th style={{ padding: '0.75rem 0.5rem' }}>Signal Role</th>
                </tr>
              </thead>
              <tbody style={{ color: '#e2e8f0' }}>
                {visual_risk?.breakdown &&
                  Object.entries(visual_risk.breakdown).map(([key, item], idx) => (
                    <tr key={key} style={{ borderBottom: '1px solid #1e293b' }}>
                      <td style={{ padding: '0.75rem 0.5rem', fontWeight: 600 }}>{item.label}</td>
                      <td style={{ padding: '0.75rem 0.5rem' }}>{item.score} / 100</td>
                      <td style={{ padding: '0.75rem 0.5rem' }}>{Math.round(item.weight * 100)}%</td>
                      <td style={{ padding: '0.75rem 0.5rem', color: '#60a5fa', fontWeight: 700 }}>
                        +{item.weighted_contribution}
                      </td>
                      <td style={{ padding: '0.75rem 0.5rem', fontSize: '0.75rem', color: '#94a3b8' }}>
                        {key === 'synthetic_signal' ? 'Supporting risk signal' : 'Primary visual contradiction metric'}
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>

          <div style={{ marginTop: '1.5rem', background: '#0f172a', padding: '1rem 1.25rem', borderRadius: '8px', border: '1px solid #334155' }}>
            <div style={{ fontSize: '0.85rem', color: '#cbd5e1' }}>
              <strong>Fusion Formula:</strong> Final Risk combines Simulated Existing Risk ({text_risk?.text_risk_score}/100) and Visual Evidence Risk ({visual_risk?.visual_risk_score}/100).
              When multiple independent visual contradictions are detected, visual risk corroboration overrides text disclosures, resulting in a final score of <strong>{fusion?.final_risk_score}/100 ({fusion?.status_label})</strong>.
            </div>
          </div>
        </div>
      )}

      {/* Tab 4: Technical Provenance & Analysis Details */}
      {activeTab === 'provenance' && (
        <div>
          <h4 style={{ color: '#f8fafc', marginBottom: '0.25rem' }}>Technical Provenance & Analysis Details</h4>
          <p style={{ color: '#94a3b8', fontSize: '0.82rem', marginBottom: '1.25rem' }}>
            Full system audit trail: Vision backbone models, candidate evidence search metrics, and active forensic filters.
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
            <div style={{ background: '#0f172a', padding: '1.25rem', borderRadius: '8px', border: '1px solid #334155' }}>
              <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: '#94a3b8', fontWeight: 700, marginBottom: '0.5rem' }}>
                Vision Model Backbone
              </div>
              <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#60a5fa' }}>
                {provenance?.vision_model || 'Vision Transformer (ViT-B/16)'}
              </div>
              <div style={{ fontSize: '0.78rem', color: '#cbd5e1', marginTop: '0.4rem' }}>
                {provenance?.is_fallback_extractor
                  ? '⚠️ Fallback feature extractor active.'
                  : '✅ Full 768-dimensional pretrained ViT patch-16 embedding model active.'}
              </div>
            </div>

            <div style={{ background: '#0f172a', padding: '1.25rem', borderRadius: '8px', border: '1px solid #334155' }}>
              <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: '#94a3b8', fontWeight: 700, marginBottom: '0.5rem' }}>
                Evidence Discovery Metrics
              </div>
              <div style={{ fontSize: '0.85rem', color: '#e2e8f0', lineHeight: '1.6' }}>
                <div>• Total Merchant Assets Analyzed: <strong>{provenance?.images_analyzed ?? 1}</strong></div>
                <div>• Candidate Evidence Discovered: <strong>{provenance?.online_evidence_candidates ?? 0}</strong></div>
                <div>• Evidence Sources: <strong>{provenance?.evidence_sources?.join(' & ') || 'ONLINE / LOCAL DEMO'}</strong></div>
              </div>
            </div>
          </div>

          <div style={{ background: '#0f172a', padding: '1.25rem', borderRadius: '8px', border: '1px solid #334155' }}>
            <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: '#94a3b8', fontWeight: 700, marginBottom: '0.5rem' }}>
              Active Visual & Forensic Signals
            </div>
            <ul style={{ paddingLeft: '1.2rem', color: '#cbd5e1', fontSize: '0.82rem', lineHeight: '1.6' }}>
              {provenance?.visual_signals?.map((s, idx) => (
                <li key={idx}>{s}</li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Tab 5: JSON Export */}
      {activeTab === 'json' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h4 style={{ color: '#f8fafc', margin: 0 }}>Structured Evidence Dossier & JSON Export</h4>
            <button type="button" className="btn-secondary" onClick={downloadJsonReport} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.8rem' }}>
              <Download size={14} />
              Download Audit JSON
            </button>
          </div>

          <pre
            style={{
              background: '#020617',
              padding: '1.25rem',
              borderRadius: '8px',
              border: '1px solid #1e293b',
              color: '#38bdf8',
              fontSize: '0.75rem',
              maxHeight: '400px',
              overflowY: 'auto',
              fontFamily: 'monospace',
            }}
          >
            {JSON.stringify(
              {
                merchant_name: fusion.merchant_name,
                final_risk_score: fusion.final_risk_score,
                status: fusion.status,
                claims_reasoning: claims_reasoning,
                structured_evidence: structured_evidence,
                provenance: provenance,
                text_risk: text_risk,
                visual_risk: visual_risk,
              },
              null,
              2
            )}
          </pre>
        </div>
      )}
    </div>
  );
}
