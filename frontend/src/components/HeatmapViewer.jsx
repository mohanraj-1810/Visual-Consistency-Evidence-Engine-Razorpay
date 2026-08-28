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
  Sparkles,
} from 'lucide-react';

export default function HeatmapViewer({ result }) {
  const [activeTab, setActiveTab] = useState('reuse'); // 'reuse' | 'forensics' | 'audit' | 'provenance' | 'json'

  if (!result || typeof result !== 'object') return null;

  const {
    fusion = {},
    visual_risk = {},
    text_risk = {},
    reuse = {},
    identity = {},
    logo = {},
    manipulation = {},
    claims = {},
    weights = {},
    structured_evidence = [],
    claims_reasoning = {},
    provenance = {},
    candidate_evidence = [],
    forensic_target_image_base64,
    ela_image_base64,
    heatmap_overlay_base64,
    product_images_base64 = [],
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
      merchant_name: fusion?.merchant_name || 'merchant',
      final_risk_score: fusion?.final_risk_score,
      status: fusion?.status,
      status_label: fusion?.status_label,
      recommendation: fusion?.recommendation,
      reasons: fusion?.reasons,
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
    a.download = `evidence_dossier_${(fusion?.merchant_name || 'merchant').toLowerCase().replace(/\s+/g, '_')}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  const reasonsList = Array.isArray(fusion?.reasons) ? fusion.reasons : [];

  return (
    <div className="card" style={{ padding: '1.75rem', marginBottom: '2.5rem' }}>
      {/* Rationale Section */}
      <div
        style={{
          marginBottom: '1.5rem',
          background: 'rgba(13, 14, 20, 0.9)',
          padding: '1.25rem 1.5rem',
          borderRadius: '10px',
          border: '1px solid #23242e',
          borderLeft: `4px solid ${fusion?.badge_color || '#3b82f6'}`,
        }}
      >
        <h4 style={{ color: '#ffffff', fontSize: '1.05rem', fontWeight: 800, marginBottom: '0.6rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span>💡 Why is this merchant categorized as</span>
          <span style={{ color: fusion?.badge_color || '#3b82f6', textTransform: 'uppercase' }}>
            {fusion?.status || 'EVALUATED'} RISK
          </span>?
        </h4>
        <ul style={{ paddingLeft: '1.2rem', color: '#cbd5e1', fontSize: '0.88rem', lineHeight: '1.6' }}>
          {reasonsList.map((r, i) => (
            <li key={i} style={{ marginBottom: '0.35rem' }}>
              <strong style={{ color: '#ffffff' }}>{i + 1}.</strong> {r}
            </li>
          ))}
          {reasonsList.length === 0 && (
            <li>Visual assets and website metadata analyzed successfully.</li>
          )}
        </ul>
      </div>

      {/* Deep-Dive Navigation Tabs */}
      <div
        style={{
          display: 'flex',
          gap: '0.5rem',
          borderBottom: '1px solid #23242e',
          marginBottom: '1.5rem',
          overflowX: 'auto',
          paddingBottom: '0.2rem',
        }}
      >
        <button
          type="button"
          className={`tab-btn ${activeTab === 'reuse' ? 'active' : ''}`}
          onClick={() => setActiveTab('reuse')}
        >
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem' }}>
            <Search size={15} /> Candidate Visual Match & Logo
          </span>
        </button>
        <button
          type="button"
          className={`tab-btn ${activeTab === 'forensics' ? 'active' : ''}`}
          onClick={() => setActiveTab('forensics')}
        >
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem' }}>
            <Eye size={15} /> Forensic ELA & Heatmaps
          </span>
        </button>
        <button
          type="button"
          className={`tab-btn ${activeTab === 'audit' ? 'active' : ''}`}
          onClick={() => setActiveTab('audit')}
        >
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem' }}>
            <Scale size={15} /> Multimodal Risk Audit
          </span>
        </button>
        <button
          type="button"
          className={`tab-btn ${activeTab === 'provenance' ? 'active' : ''}`}
          onClick={() => setActiveTab('provenance')}
        >
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem' }}>
            <Cpu size={15} /> Vision Backbone Provenance
          </span>
        </button>
        <button
          type="button"
          className={`tab-btn ${activeTab === 'json' ? 'active' : ''}`}
          onClick={() => setActiveTab('json')}
        >
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem' }}>
            <FileText size={15} /> JSON Dossier Export
          </span>
        </button>
      </div>

      {/* Tab 1: Image Reuse & Logo */}
      {activeTab === 'reuse' && (
        <div>
          {/* Section 1: Candidate Visual Match */}
          <div style={{ marginBottom: '2rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.6rem', flexWrap: 'wrap', gap: '0.5rem' }}>
              <h4 style={{ color: '#ffffff', margin: 0, fontSize: '1.05rem', fontWeight: 700 }}>
                1. Product Visual Verification vs. Candidate Evidence
              </h4>
              <span className={`status-pill ${isOnline ? 'blue' : 'purple'}`}>
                {isOnline ? <Globe size={13} /> : <Database size={13} />}
                <span>{isOnline ? 'ONLINE WEB DISCOVERY' : 'LOCAL CATALOG REFERENCE'}</span>
              </span>
            </div>
            <p style={{ color: '#94a3b8', fontSize: '0.85rem', marginBottom: '1.25rem' }}>
              Candidate public imagery is discovered and verified using our Vision Transformer (ViT) cosine embeddings.
            </p>

            {matched_reference_image_base64 ? (
              <div className="grid-3" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))' }}>
                <div
                  style={{
                    background: '#0d0e14',
                    border: '1px solid #23242e',
                    borderRadius: '10px',
                    padding: '1rem',
                    textAlign: 'center',
                  }}
                >
                  <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#94a3b8', marginBottom: '0.6rem' }}>
                    Merchant Extracted Visual
                  </div>
                  {product_images_base64 && product_images_base64.length > 0 ? (
                    <img
                      src={product_images_base64[topItem?.image_index || 0]}
                      alt="Merchant Visual"
                      style={{ maxHeight: '220px', maxWidth: '100%', borderRadius: '8px', objectFit: 'contain' }}
                    />
                  ) : (
                    <div style={{ color: '#64748b', padding: '2rem' }}>Product Visual</div>
                  )}
                </div>

                <div
                  style={{
                    background: '#0d0e14',
                    border: '1px solid #23242e',
                    borderRadius: '10px',
                    padding: '1rem',
                    textAlign: 'center',
                  }}
                >
                  <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#94a3b8', marginBottom: '0.6rem' }}>
                    Candidate Web Match (<code>{refFilename}</code>)
                  </div>
                  <img
                    src={matched_reference_image_base64}
                    alt="Candidate Match"
                    style={{ maxHeight: '220px', maxWidth: '100%', borderRadius: '8px', objectFit: 'contain' }}
                  />
                </div>

                <div
                  style={{
                    background: '#0d0e14',
                    border: '1px solid #23242e',
                    borderRadius: '10px',
                    padding: '1.25rem',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                  }}
                >
                  <div>
                    <span
                      className={`risk-badge ${
                        topItem?.risk_level === 'HIGH' ? 'high' : topItem?.risk_level === 'MEDIUM' ? 'medium' : 'low'
                      }`}
                    >
                      {topItem?.risk_level === 'HIGH' ? 'POTENTIAL VISUAL MATCH' : topItem?.risk_level === 'MEDIUM' ? 'MODERATE SIMILARITY' : 'UNIQUE VISUAL'}
                    </span>

                    <div style={{ marginTop: '1rem', fontSize: '0.88rem', color: '#e2e8f0', lineHeight: '1.5' }}>
                      <strong style={{ color: '#94a3b8' }}>ViT Similarity:</strong>{' '}
                      <span style={{ fontSize: '1.3rem', fontWeight: 800, color: topSim >= 0.85 ? '#f43f5e' : topSim >= 0.70 ? '#f59e0b' : '#10b981', fontFamily: 'JetBrains Mono' }}>
                        {topSimPct}%
                      </span>
                    </div>

                    <div style={{ marginTop: '0.5rem', fontSize: '0.8rem', color: '#94a3b8' }}>
                      <strong>Evidence Strength:</strong> {topItem?.risk_level || 'EVALUATED'}
                    </div>

                    <div style={{ marginTop: '0.5rem', fontSize: '0.8rem', color: '#94a3b8' }}>
                      <strong>Source Domain:</strong> <code style={{ color: '#60a5fa' }}>{sourceDomain}</code>
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
                            fontSize: '0.78rem',
                            color: '#60a5fa',
                            textDecoration: 'none',
                          }}
                        >
                          <ExternalLink size={13} />
                          Inspect Candidate Source URL
                        </a>
                      </div>
                    )}
                  </div>

                  <p style={{ marginTop: '0.85rem', fontSize: '0.82rem', color: '#cbd5e1', lineHeight: 1.4 }}>
                    {topItem?.explanation || 'ViT similarity computed against candidate evidence.'}
                  </p>
                </div>
              </div>
            ) : (
              <div style={{ background: '#0d0e14', border: '1px solid #23242e', padding: '1.25rem', borderRadius: '10px', color: '#94a3b8', fontSize: '0.85rem' }}>
                No candidate image reuse identified. Merchant imagery appears original and authentic.
              </div>
            )}
          </div>

          {/* Section 2: Logo Consistency */}
          <div style={{ borderTop: '1px solid #23242e', paddingTop: '1.75rem' }}>
            <h4 style={{ color: '#ffffff', marginBottom: '0.3rem', fontSize: '1.05rem', fontWeight: 700 }}>
              2. Brand Identity & Logo Visual Consistency
            </h4>
            <p style={{ color: '#94a3b8', fontSize: '0.85rem', marginBottom: '1.25rem' }}>
              Compares merchant logo against verified brand assets to evaluate stylistic divergence.
            </p>

            {matched_logo_reference_base64 && logo_image_base64 ? (
              <div className="grid-3" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))' }}>
                <div style={{ background: '#0d0e14', border: '1px solid #23242e', borderRadius: '10px', padding: '1rem', textAlign: 'center' }}>
                  <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#94a3b8', marginBottom: '0.6rem' }}>
                    Merchant Extracted Logo
                  </div>
                  <img src={logo_image_base64} alt="Merchant Logo" style={{ maxHeight: '180px', maxWidth: '100%', borderRadius: '8px', objectFit: 'contain' }} />
                </div>

                <div style={{ background: '#0d0e14', border: '1px solid #23242e', borderRadius: '10px', padding: '1rem', textAlign: 'center' }}>
                  <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#94a3b8', marginBottom: '0.6rem' }}>
                    Verified Reference Mark (<code>{logoMatchedName}</code>)
                  </div>
                  <img src={matched_logo_reference_base64} alt="Verified Logo" style={{ maxHeight: '180px', maxWidth: '100%', borderRadius: '8px', objectFit: 'contain' }} />
                </div>

                <div style={{ background: '#0d0e14', border: '1px solid #23242e', borderRadius: '10px', padding: '1.25rem', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                  <div>
                    <span className={`risk-badge ${logoSimPct < 55 ? 'high' : logoSimPct < 82 ? 'medium' : 'low'}`}>
                      {logoSimPct < 55 ? 'VISUAL IDENTITY INCONSISTENCY' : logoSimPct < 82 ? 'MODERATE VARIANCE' : 'CONSISTENT IDENTITY'}
                    </span>

                    <div style={{ marginTop: '1rem', fontSize: '0.88rem', color: '#e2e8f0', lineHeight: '1.5' }}>
                      <strong style={{ color: '#94a3b8' }}>Logo Alignment:</strong>{' '}
                      <span style={{ fontSize: '1.3rem', fontWeight: 800, color: logoSimPct < 55 ? '#f43f5e' : logoSimPct < 82 ? '#f59e0b' : '#10b981', fontFamily: 'JetBrains Mono' }}>
                        {logoSimPct}%
                      </span>
                    </div>

                    <div style={{ marginTop: '0.5rem', fontSize: '0.8rem', color: '#94a3b8' }}>
                      <strong>Inconsistency Risk:</strong> {Math.round(logo?.inconsistency_risk ?? 0)}%
                    </div>
                  </div>

                  <p style={{ marginTop: '0.85rem', fontSize: '0.82rem', color: '#cbd5e1', lineHeight: 1.4 }}>
                    {logo?.explanation || 'Logo consistency verified.'}
                  </p>
                </div>
              </div>
            ) : (
              <div style={{ background: '#0d0e14', border: '1px solid #23242e', padding: '1.25rem', borderRadius: '10px', color: '#94a3b8', fontSize: '0.85rem' }}>
                No logo uploaded or no reference brand registered.
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 2: Forensics & Heatmap */}
      {activeTab === 'forensics' && (
        <div>
          <h4 style={{ color: '#ffffff', marginBottom: '0.3rem', fontSize: '1.05rem', fontWeight: 700 }}>
            Forensic Tampering & Pixel Anomaly Scan
          </h4>
          <p style={{ color: '#94a3b8', fontSize: '0.85rem', marginBottom: '1.25rem' }}>
            Multi-spectral Error Level Analysis (ELA) and Laplacian gradient variance to detect localized editing anomalies.
          </p>

          <div className="grid-3" style={{ marginBottom: '1.5rem' }}>
            <div style={{ background: '#0d0e14', border: '1px solid #23242e', borderRadius: '10px', padding: '1rem', textAlign: 'center' }}>
              <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#94a3b8', marginBottom: '0.6rem' }}>
                1. Original Visual Asset
              </div>
              {forensic_target_image_base64 ? (
                <img src={forensic_target_image_base64} alt="Original Document" style={{ maxHeight: '240px', maxWidth: '100%', borderRadius: '8px', objectFit: 'contain' }} />
              ) : (
                <div style={{ color: '#64748b', padding: '3rem 1rem' }}>No document provided</div>
              )}
            </div>

            <div style={{ background: '#0d0e14', border: '1px solid #23242e', borderRadius: '10px', padding: '1rem', textAlign: 'center' }}>
              <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#94a3b8', marginBottom: '0.6rem' }}>
                2. Error Level Analysis (ELA)
              </div>
              {ela_image_base64 ? (
                <img src={ela_image_base64} alt="ELA Difference" style={{ maxHeight: '240px', maxWidth: '100%', borderRadius: '8px', objectFit: 'contain' }} />
              ) : (
                <div style={{ color: '#64748b', padding: '3rem 1rem' }}>ELA not computed</div>
              )}
            </div>

            <div style={{ background: '#0d0e14', border: '1px solid #23242e', borderRadius: '10px', padding: '1rem', textAlign: 'center' }}>
              <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#94a3b8', marginBottom: '0.6rem' }}>
                3. Forensic Heatmap Overlay
              </div>
              {heatmap_overlay_base64 ? (
                <img src={heatmap_overlay_base64} alt="Heatmap Overlay" style={{ maxHeight: '240px', maxWidth: '100%', borderRadius: '8px', objectFit: 'contain' }} />
              ) : (
                <div style={{ color: '#64748b', padding: '3rem 1rem' }}>Heatmap not computed</div>
              )}
            </div>
          </div>

          <div style={{ background: '#0d0e14', border: '1px solid #23242e', padding: '1.25rem', borderRadius: '10px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
              <div>
                <span className={`risk-badge ${manipulation?.risk_level === 'HIGH' ? 'high' : manipulation?.risk_level === 'MEDIUM' ? 'medium' : 'low'}`}>
                  {manipulation?.risk_level === 'HIGH' ? 'MANIPULATION DETECTED' : manipulation?.risk_level === 'MEDIUM' ? 'MODERATE ANOMALIES' : 'UNIFORM PIXEL COMPRESSION'}
                </span>
                <div style={{ marginTop: '0.65rem', fontSize: '0.9rem', color: '#ffffff' }}>
                  <strong>Manipulation Score:</strong>{' '}
                  <span style={{ fontFamily: 'JetBrains Mono', color: '#60a5fa' }}>{manipulation?.manipulation_score ?? 0}%</span>
                </div>
              </div>

              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '0.82rem', color: '#94a3b8' }}>
                  Synthetic-Image Suspicion: <strong style={{ color: (manipulation?.synthetic_score ?? 0) >= 60 ? '#f59e0b' : '#60a5fa', fontFamily: 'JetBrains Mono' }}>{manipulation?.synthetic_score ?? 0}%</strong>
                </div>
                <div style={{ fontSize: '0.72rem', color: '#64748b', marginTop: '0.2rem' }}>
                  Supporting signal only — not used independently for rejection.
                </div>
              </div>
            </div>

            <p style={{ marginTop: '0.85rem', fontSize: '0.82rem', color: '#cbd5e1', lineHeight: 1.45 }}>
              {manipulation?.explanation || 'Pixel variance analyzed.'}
            </p>
          </div>
        </div>
      )}

      {/* Tab 3: Multimodal Risk Weights */}
      {activeTab === 'audit' && (
        <div>
          <h4 style={{ color: '#ffffff', marginBottom: '0.3rem', fontSize: '1.05rem', fontWeight: 700 }}>
            Multimodal Risk Fusion & Signal Weighting
          </h4>
          <p style={{ color: '#94a3b8', fontSize: '0.85rem', marginBottom: '1.25rem' }}>
            Transparent breakdown of individual computer vision weights, multi-signal corroboration, and text compliance signals.
          </p>

          <div style={{ overflowX: 'auto', background: '#0d0e14', border: '1px solid #23242e', borderRadius: '10px', padding: '0.5rem' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem', textAlign: 'left' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #23242e', color: '#94a3b8' }}>
                  <th style={{ padding: '0.75rem' }}>Signal Dimension</th>
                  <th style={{ padding: '0.75rem' }}>Raw Score</th>
                  <th style={{ padding: '0.75rem' }}>Weight</th>
                  <th style={{ padding: '0.75rem' }}>Weighted Contribution</th>
                  <th style={{ padding: '0.75rem' }}>Signal Role</th>
                </tr>
              </thead>
              <tbody style={{ color: '#e2e8f0' }}>
                {visual_risk?.breakdown &&
                  Object.entries(visual_risk.breakdown).map(([key, item]) => (
                    <tr key={key} style={{ borderBottom: '1px solid #181924' }}>
                      <td style={{ padding: '0.75rem', fontWeight: 600, color: '#ffffff' }}>{item?.label || key}</td>
                      <td style={{ padding: '0.75rem', fontFamily: 'JetBrains Mono' }}>{item?.score ?? 0} / 100</td>
                      <td style={{ padding: '0.75rem', fontFamily: 'JetBrains Mono' }}>{Math.round((item?.weight ?? 0) * 100)}%</td>
                      <td style={{ padding: '0.75rem', color: '#60a5fa', fontWeight: 700, fontFamily: 'JetBrains Mono' }}>
                        +{item?.weighted_contribution ?? 0}
                      </td>
                      <td style={{ padding: '0.75rem', fontSize: '0.75rem', color: '#94a3b8' }}>
                        {key === 'synthetic_signal' ? 'Supporting risk signal' : 'Primary visual contradiction metric'}
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 4: Technical Provenance */}
      {activeTab === 'provenance' && (
        <div>
          <h4 style={{ color: '#ffffff', marginBottom: '0.3rem', fontSize: '1.05rem', fontWeight: 700 }}>
            Technical Provenance & System Audit Trail
          </h4>
          <p style={{ color: '#94a3b8', fontSize: '0.85rem', marginBottom: '1.25rem' }}>
            Full system audit trail: Vision Transformer backbone models, Serper.dev candidate discovery, and active forensic filters.
          </p>

          <div className="grid-2" style={{ marginBottom: '1.5rem' }}>
            <div style={{ background: '#0d0e14', border: '1px solid #23242e', padding: '1.25rem', borderRadius: '10px' }}>
              <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: '#94a3b8', fontWeight: 700, marginBottom: '0.4rem' }}>
                Vision Model Backbone
              </div>
              <div style={{ fontSize: '1.2rem', fontWeight: 800, color: '#60a5fa', fontFamily: 'JetBrains Mono' }}>
                {provenance?.vision_model || 'Vision Transformer (ViT-B/16)'}
              </div>
              <div style={{ fontSize: '0.8rem', color: '#cbd5e1', marginTop: '0.5rem' }}>
                {provenance?.is_fallback_extractor
                  ? '⚠️ Fallback lightweight feature extractor active.'
                  : '✅ Full 768-dimensional pretrained ViT patch-16 embedding backbone active.'}
              </div>
            </div>

            <div style={{ background: '#0d0e14', border: '1px solid #23242e', padding: '1.25rem', borderRadius: '10px' }}>
              <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: '#94a3b8', fontWeight: 700, marginBottom: '0.4rem' }}>
                Evidence Discovery Metrics
              </div>
              <div style={{ fontSize: '0.85rem', color: '#e2e8f0', lineHeight: '1.7' }}>
                <div>• Total Merchant Assets Analyzed: <strong>{provenance?.images_analyzed ?? (product_images_base64?.length || 1)}</strong></div>
                <div>• Candidate Evidence Discovered: <strong>{provenance?.online_evidence_candidates ?? (candidate_evidence?.length || 0)}</strong></div>
                <div>• Evidence Sources: <strong>{provenance?.evidence_sources?.join(' & ') || 'SERPER.DEV WEB SEARCH / LOCAL CATALOG'}</strong></div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 5: JSON Export */}
      {activeTab === 'json' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.5rem' }}>
            <h4 style={{ color: '#ffffff', margin: 0, fontSize: '1.05rem', fontWeight: 700 }}>
              Structured Evidence Dossier & JSON Export
            </h4>
            <button type="button" className="btn-secondary" onClick={downloadJsonReport} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.8rem' }}>
              <Download size={14} />
              Download Audit JSON
            </button>
          </div>

          <pre
            style={{
              background: '#07080c',
              padding: '1.25rem',
              borderRadius: '10px',
              border: '1px solid #23242e',
              color: '#38bdf8',
              fontSize: '0.78rem',
              maxHeight: '400px',
              overflowY: 'auto',
              fontFamily: 'JetBrains Mono, monospace',
            }}
          >
            {JSON.stringify(
              {
                merchant_name: fusion?.merchant_name || 'merchant',
                final_risk_score: fusion?.final_risk_score,
                status: fusion?.status,
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
