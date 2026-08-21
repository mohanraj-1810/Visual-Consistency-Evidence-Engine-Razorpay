import React, { useState } from 'react';
import { Search, Eye, Scale, Download, FileText, CheckCircle2, AlertTriangle, ShieldAlert } from 'lucide-react';

export default function HeatmapViewer({ result }) {
  const [activeTab, setActiveTab] = useState('reuse'); // 'reuse' | 'forensics' | 'audit' | 'json'

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
  const refFilename = topItem?.reference_filename ?? 'None';

  const downloadJsonReport = () => {
    const exportData = {
      timestamp: new Date().toISOString(),
      merchant_name: fusion.merchant_name,
      final_risk_score: fusion.final_risk_score,
      status: fusion.status,
      status_label: fusion.status_label,
      recommendation: fusion.recommendation,
      reasons: fusion.reasons,
      claims_vs_visual_evidence: {
        inventory_claim: claims?.inventory_claim,
        inventory_visual_similarity: topSim,
        brand_claim: claims?.brand_claim,
        logo_consistency_score: logo?.consistency_score,
        compliance_claim: claims?.compliance_claim,
        manipulation_score: manipulation?.manipulation_score,
      },
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
    a.download = `risk_report_${(fusion.merchant_name || 'merchant').toLowerCase().replace(/\s+/g, '_')}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  return (
    <div className="card" style={{ padding: '1.5rem', marginBottom: '2rem' }}>
      {/* Rationale Section */}
      <div style={{ marginBottom: '1.5rem', background: '#0f172a', padding: '1rem 1.25rem', borderRadius: '8px', border: '1px solid #334155' }}>
        <h4 style={{ color: '#f8fafc', fontSize: '1rem', fontWeight: 700, marginBottom: '0.6rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
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
          🔍 Image Reuse & Logo Side-by-Side
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
          className={`deepdive-tab-btn ${activeTab === 'json' ? 'active' : ''}`}
          onClick={() => setActiveTab('json')}
        >
          <FileText size={16} />
          📄 Audit Inspector & JSON Export
        </button>
      </div>

      {/* Tab 1: Image Reuse & Logo */}
      {activeTab === 'reuse' && (
        <div>
          <div style={{ marginBottom: '1.75rem' }}>
            <h4 style={{ color: '#f8fafc', marginBottom: '0.25rem' }}>1. Image Reuse Evidence</h4>
            <p style={{ color: '#94a3b8', fontSize: '0.82rem', marginBottom: '1rem' }}>
              Compares merchant product images against verified reference catalog using Vision Transformer (ViT) embeddings.
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
                    Matched Catalog Reference (<code>{refFilename}</code>)
                  </div>
                  <img src={matched_reference_image_base64} alt="Catalog Reference" />
                </div>

                <div style={{ background: '#0f172a', padding: '1.25rem', borderRadius: '8px', border: '1px solid #334155' }}>
                  <span className={`evidence-tag ${topItem?.risk_level === 'HIGH' ? 'tag-red' : 'tag-amber'}`}>
                    {topItem?.risk_level} REUSE RISK
                  </span>
                  <h4 style={{ color: '#f8fafc', margin: '0.4rem 0' }}>
                    Cosine Similarity: {Math.round(topSim * 100)}%
                  </h4>
                  <p style={{ fontSize: '0.82rem', color: '#94a3b8', marginBottom: '0.6rem' }}>
                    <strong>WHAT WAS FOUND:</strong><br />
                    {topItem?.explanation}
                  </p>
                  <p style={{ fontSize: '0.82rem', color: '#94a3b8', marginBottom: '0.6rem' }}>
                    <strong>WHY IT MATTERS:</strong><br />
                    Duplicated catalog photos indicate potential inventory misrepresentation or unauthorized drop-shipping.
                  </p>
                  <p style={{ fontSize: '0.82rem', color: '#94a3b8' }}>
                    <strong>CONFIDENCE SCORE:</strong><br />
                    ViT embedding similarity = <code>{topSim}</code>
                  </p>
                </div>
              </div>
            ) : (
              <div style={{ background: '#0f172a', padding: '1rem', borderRadius: '8px', color: '#94a3b8', fontSize: '0.85rem' }}>
                No catalog reference matches flagged. Product visuals appear authentic to reference catalog.
              </div>
            )}
          </div>

          <hr style={{ borderColor: '#334155', margin: '1.5rem 0' }} />

          <div>
            <h4 style={{ color: '#f8fafc', marginBottom: '0.25rem' }}>2. Logo & Brand Identity Consistency</h4>
            <p style={{ color: '#94a3b8', fontSize: '0.82rem', marginBottom: '1rem' }}>
              Compares merchant logo against verified brand repository.
            </p>

            <div className="comparison-grid">
              <div className="image-preview-box">
                <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#94a3b8', marginBottom: '0.5rem' }}>
                  Merchant Provided Logo
                </div>
                {logo_image_base64 ? (
                  <img src={logo_image_base64} alt="Merchant Logo" />
                ) : (
                  <div style={{ color: '#64748b', padding: '2rem' }}>No logo provided</div>
                )}
              </div>

              <div className="image-preview-box">
                <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#94a3b8', marginBottom: '0.5rem' }}>
                  Verified Official Asset (<code>{logo?.matched_reference || 'None'}</code>)
                </div>
                {matched_logo_reference_base64 ? (
                  <img src={matched_logo_reference_base64} alt="Verified Logo" />
                ) : (
                  <div style={{ color: '#64748b', padding: '2rem' }}>No matching brand logo</div>
                )}
              </div>

              <div style={{ background: '#0f172a', padding: '1.25rem', borderRadius: '8px', border: '1px solid #334155' }}>
                <span
                  className={`evidence-tag ${
                    logo?.risk_level === 'HIGH' ? 'tag-red' : logo?.risk_level === 'MEDIUM' ? 'tag-amber' : 'tag-green'
                  }`}
                >
                  {logo?.risk_level} INCONSISTENCY
                </span>
                <h4 style={{ color: '#f8fafc', margin: '0.4rem 0' }}>
                  Consistency Score: {logo?.consistency_score}%
                </h4>
                <p style={{ fontSize: '0.82rem', color: '#94a3b8', marginBottom: '0.6rem' }}>
                  <strong>EVALUATION:</strong><br />
                  {logo?.explanation}
                </p>
                <p style={{ fontSize: '0.82rem', color: '#94a3b8' }}>
                  <strong>POLICY NOTICE:</strong><br />
                  Identifies visual stylistic variance. Does not claim trademark infringement or fraud.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Forensic Manipulation & Heatmap */}
      {activeTab === 'forensics' && (
        <div>
          <div style={{ marginBottom: '1rem' }}>
            <h4 style={{ color: '#f8fafc', marginBottom: '0.25rem' }}>Image Forensic Analysis & Explainable Heatmap</h4>
            <p style={{ color: '#94a3b8', fontSize: '0.82rem' }}>
              Uses Error Level Analysis (ELA) and Laplacian gradient variance to highlight suspicious compression discrepancies and spliced regions.
            </p>
          </div>

          {forensic_target_image_base64 ? (
            <div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1.25rem', marginBottom: '1.5rem' }}>
                <div className="image-preview-box">
                  <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#94a3b8', marginBottom: '0.5rem' }}>
                    1. Original Document / Visual
                  </div>
                  <img src={forensic_target_image_base64} alt="Original Analyzed Visual" />
                </div>

                <div className="image-preview-box">
                  <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#94a3b8', marginBottom: '0.5rem' }}>
                    2. Error Level Analysis (ELA)
                  </div>
                  <img src={ela_image_base64} alt="ELA Image" />
                  <div style={{ fontSize: '0.72rem', color: '#64748b', marginTop: '0.4rem' }}>
                    Bright high-contrast patches reveal localized re-compression anomalies.
                  </div>
                </div>

                <div className="image-preview-box">
                  <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#94a3b8', marginBottom: '0.5rem' }}>
                    3. Explainable Forensic Heatmap
                  </div>
                  <img src={heatmap_overlay_base64} alt="Forensic Heatmap" />
                  <div style={{ fontSize: '0.72rem', color: '#64748b', marginTop: '0.4rem' }}>
                    Red/amber zones indicate high anomaly density and bounding box overlays.
                  </div>
                </div>
              </div>

              <div style={{ background: '#0f172a', padding: '1.25rem', borderRadius: '8px', border: '1px solid #334155' }}>
                <span
                  className={`evidence-tag ${
                    manipulation?.risk_level === 'HIGH' ? 'tag-red' : manipulation?.risk_level === 'MEDIUM' ? 'tag-amber' : 'tag-green'
                  }`}
                >
                  FORENSIC SCORE: {manipulation?.manipulation_score}% ({manipulation?.risk_level})
                </span>
                <p style={{ fontSize: '0.9rem', color: '#e2e8f0', margin: '0.5rem 0' }}>
                  <strong>Forensic Finding:</strong> {manipulation?.explanation}
                </p>
                <p style={{ fontSize: '0.82rem', color: '#94a3b8', marginBottom: '0.4rem' }}>
                  <strong>Synthetic-Image Suspicion (Supporting Signal):</strong> {manipulation?.synthetic_score}% — {manipulation?.synthetic_desc}
                </p>
                <p style={{ fontSize: '0.75rem', color: '#64748b', fontStyle: 'italic' }}>
                  Disclaimer: Visual forensic signals indicate compression and edge variances. They do not constitute absolute proof of tampering.
                </p>
              </div>
            </div>
          ) : (
            <div style={{ background: '#0f172a', padding: '1.5rem', borderRadius: '8px', color: '#94a3b8' }}>
              No document or visual uploaded for forensic inspection.
            </div>
          )}
        </div>
      )}

      {/* Tab 3: Weights & Audit */}
      {activeTab === 'audit' && (
        <div>
          <h4 style={{ color: '#f8fafc', marginBottom: '0.5rem' }}>Visual Dimension Weights Allocation</h4>
          <table className="custom-table">
            <thead>
              <tr>
                <th>Visual Signal Dimension</th>
                <th>Raw Score (0-100)</th>
                <th>Weight</th>
                <th>Weighted Contribution</th>
              </tr>
            </thead>
            <tbody>
              {visual_risk?.breakdown &&
                Object.entries(visual_risk.breakdown).map(([key, v]) => (
                  <tr key={key}>
                    <td><strong>{v.label}</strong></td>
                    <td>{v.score}%</td>
                    <td>{Math.round(v.weight * 100)}%</td>
                    <td><code style={{ color: '#a5b4fc' }}>{v.weighted_contribution}</code></td>
                  </tr>
                ))}
            </tbody>
          </table>

          <hr style={{ borderColor: '#334155', margin: '1.5rem 0' }} />

          <h4 style={{ color: '#f8fafc', marginBottom: '0.5rem' }}>Fusion Formula Audit</h4>
          <div
            style={{
              background: '#0f172a',
              padding: '1rem',
              borderRadius: '8px',
              border: '1px solid #334155',
              fontFamily: 'JetBrains Mono, monospace',
              fontSize: '0.82rem',
              color: '#a5b4fc',
              lineHeight: '1.6',
            }}
          >
            Text Risk Score = {fusion.text_risk_score} / 100<br />
            Visual Risk Score = {fusion.visual_risk_score} / 100<br /><br />
            Formula Mode:{' '}
            {fusion.visual_risk_score >= 70 && fusion.text_risk_score < 40
              ? 'Deceptive Visual Contrast Escalation (0.80 * Visual + 0.20 * Text)'
              : 'Standard Multimodal Signal Fusion (0.60 * Visual + 0.40 * Text)'}
            <br />
            Final Fused Risk = <strong>{fusion.final_risk_score} / 100</strong> → <span style={{ color: fusion.badge_color }}>{fusion.status_label}</span>
          </div>
        </div>
      )}

      {/* Tab 4: JSON Inspector */}
      {activeTab === 'json' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <div>
              <h4 style={{ color: '#f8fafc' }}>Analyst Audit Log (JSON)</h4>
              <p style={{ color: '#94a3b8', fontSize: '0.8rem' }}>Structured compliance export payload.</p>
            </div>
            <button
              onClick={downloadJsonReport}
              className="btn-primary"
              style={{ width: 'auto', padding: '0.5rem 1rem', fontSize: '0.85rem' }}
            >
              <Download size={15} />
              Download JSON Report
            </button>
          </div>

          <pre
            style={{
              background: '#0a0f1d',
              padding: '1.25rem',
              borderRadius: '8px',
              border: '1px solid #334155',
              color: '#38bdf8',
              fontSize: '0.78rem',
              maxHeight: '400px',
              overflowY: 'auto',
              whiteSpace: 'pre-wrap',
            }}
          >
            {JSON.stringify(
              {
                merchant_name: fusion.merchant_name,
                final_risk_score: fusion.final_risk_score,
                status: fusion.status,
                status_label: fusion.status_label,
                recommendation: fusion.recommendation,
                reasons: fusion.reasons,
                scores: {
                  text_risk_score: text_risk?.text_risk_score,
                  visual_risk_score: visual_risk?.visual_risk_score,
                  reuse_similarity_max: reuse?.max_similarity,
                  identity_coherence_score: identity?.coherence_score,
                  logo_inconsistency: logo?.inconsistency_risk,
                  manipulation_score: manipulation?.manipulation_score,
                },
                claims: claims,
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
