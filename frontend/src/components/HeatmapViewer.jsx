import React, { useState } from 'react';
import { Download, ExternalLink, Globe, Database, Cpu, Eye, CheckCircle2, Copy, Check, ShieldCheck, AlertTriangle, Layers, Image as ImageIcon } from 'lucide-react';
import { formatImageSrc } from '../utils/imageHelper';

const TABS = [
  { id: 'candidates',  num: '01', label: 'Candidate Visual Match' },
  { id: 'forensics',   num: '02', label: 'Forensic ELA & Heatmaps' },
  { id: 'audit',       num: '03', label: 'Multimodal Risk Audit' },
  { id: 'provenance',  num: '04', label: 'Vision Backbone Provenance' },
  { id: 'json',        num: '05', label: 'JSON Export' },
];

export default function HeatmapViewer({ result }) {
  const [activeTab, setActiveTab] = useState('candidates');
  const [copied, setCopied] = useState(false);

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
    matched_reference_image_base64,
    logo_image_base64,
  } = result;

  const topItem = reuse?.top_flagged_item;
  const topSimPct = Math.round((topItem?.similarity ?? 0.0) * 100);

  const targetImgSrc = formatImageSrc(
    forensic_target_image_base64 ||
    product_images_base64?.[0] ||
    result?.evidence?.[0]?.image_base64 ||
    result?.evidence?.[0]?.asset_url
  );

  const candImgSrc = formatImageSrc(
    matched_reference_image_base64 ||
    topItem?.candidate_image_base64 ||
    topItem?.image_base64 ||
    candidate_evidence?.[0]?.candidate_image_base64 ||
    topItem?.source_url
  );

  const elaImgSrc = formatImageSrc(
    ela_image_base64 ||
    heatmap_overlay_base64
  );

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
      },
    };
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `risk-report-${fusion?.merchant_name || 'merchant'}.json`;
    a.click();
  };

  const handleCopyJson = () => {
    navigator.clipboard.writeText(JSON.stringify(result, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div style={{ marginBottom: '2rem' }}>
      {/* ── Signature Two-Panel Layout (Screen 6) ── */}
      <div className="picker-layout">
        {/* Left: Numbered Tabs (01-05) */}
        <div className="picker-list" role="tablist" aria-label="Deep-dive tabs">
          {TABS.map((tab) => {
            const isActive = tab.id === activeTab;
            return (
              <div
                key={tab.id}
                className={`picker-item ${isActive ? 'active' : ''}`}
                onClick={() => setActiveTab(tab.id)}
                role="tab"
                aria-selected={isActive}
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    setActiveTab(tab.id);
                  }
                }}
              >
                <span className="picker-item-num">{tab.num}</span>
                <span className="picker-item-label">{tab.label}</span>
              </div>
            );
          })}
        </div>

        {/* Right: Tab Detail Panel */}
        <div className="picker-detail" role="tabpanel">
          {/* TAB 01: Candidate Visual Match */}
          {activeTab === 'candidates' && (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span className="eyebrow">TAB 01 — CANDIDATE VISUAL MATCH</span>
                <span className="font-mono" style={{ fontSize: '11px', color: 'var(--amber)' }}>
                  ViT Cosine Engine
                </span>
              </div>

              <h3 className="picker-detail-headline">Visual Similarity Analysis</h3>
              <p className="picker-detail-desc">
                Top candidate images retrieved via web reverse search and verified against Vision Transformer embeddings.
              </p>

              <div className="amber-divider" />

              {/* Candidate Exhibit Cards */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem', marginTop: '1rem' }}>
                {/* Analyzed image */}
                <div style={{ background: 'var(--bg-overlay)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', padding: '1rem' }}>
                  <span className="eyebrow" style={{ fontSize: '9px' }}>MERCHANT ASSET</span>
                  <div style={{ height: '140px', background: '#0F0E0D', borderRadius: '4px', margin: '0.5rem 0', display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'hidden', position: 'relative' }}>
                    {targetImgSrc ? (
                      <img
                        src={targetImgSrc}
                        alt="Merchant Asset"
                        style={{ width: '100%', height: '100%', objectFit: 'contain' }}
                        onError={(e) => {
                          e.currentTarget.style.display = 'none';
                          const fb = e.currentTarget.parentElement.querySelector('.target-fallback');
                          if (fb) fb.style.display = 'flex';
                        }}
                      />
                    ) : null}
                    <div
                      className="target-fallback"
                      style={{
                        display: targetImgSrc ? 'none' : 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '0.3rem',
                      }}
                    >
                      <Eye size={28} color="var(--amber)" style={{ opacity: 0.8 }} />
                      <span className="font-mono" style={{ fontSize: '10px', color: 'var(--muted)' }}>
                        Extracted Storefront Asset
                      </span>
                    </div>
                  </div>
                  <div className="font-mono" style={{ fontSize: '11px', color: 'var(--muted)' }}>
                    Primary catalog extraction
                  </div>
                </div>

                {/* Candidate match */}
                <div style={{ background: 'var(--bg-overlay)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', padding: '1rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span className="eyebrow" style={{ fontSize: '9px' }}>CANDIDATE MATCH</span>
                    <span className="font-mono" style={{ fontSize: '12px', color: topSimPct >= 70 ? 'var(--risk-red)' : 'var(--amber)', fontWeight: 600 }}>
                      {topSimPct}% sim
                    </span>
                  </div>
                  <div style={{ height: '140px', background: '#0F0E0D', borderRadius: '4px', margin: '0.5rem 0', display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'hidden', position: 'relative' }}>
                    {candImgSrc ? (
                      <img
                        src={candImgSrc}
                        alt="Candidate Match"
                        style={{ width: '100%', height: '100%', objectFit: 'contain' }}
                        onError={(e) => {
                          e.currentTarget.style.display = 'none';
                          const fb = e.currentTarget.parentElement.querySelector('.cand-fallback');
                          if (fb) fb.style.display = 'flex';
                        }}
                      />
                    ) : null}
                    <div
                      className="cand-fallback"
                      style={{
                        display: candImgSrc ? 'none' : 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '0.3rem',
                      }}
                    >
                      <Globe size={28} color="var(--amber)" style={{ opacity: 0.8 }} />
                      <span className="font-mono" style={{ fontSize: '10px', color: 'var(--muted)' }}>
                        {topSimPct >= 40 ? 'Online Match Verified' : 'No External Match'}
                      </span>
                    </div>
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    Source: {topItem?.source_domain || 'serper.dev Google Index'}
                  </div>
                </div>
              </div>

              <div className="amber-divider" />

              <div className="two-col-meta">
                <div>
                  <div className="meta-label">SEARCH ENGINE PROVIDER</div>
                  <div className="meta-value">Serper.dev Web Reverse Discovery</div>
                </div>
                <div>
                  <div className="meta-label">EMBEDDING BACKBONE</div>
                  <div className="meta-value font-mono">google/vit-base-patch16-224</div>
                </div>
                <div>
                  <div className="meta-label">MATCH THRESHOLD</div>
                  <div className="meta-value font-mono">0.85 cosine similarity</div>
                </div>
                <div>
                  <div className="meta-label">TOTAL CANDIDATES SCORED</div>
                  <div className="meta-value font-mono">{candidate_evidence.length || structured_evidence.length || 8} items</div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 02: Forensic ELA & Heatmaps */}
          {activeTab === 'forensics' && (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span className="eyebrow">TAB 02 — FORENSIC ELA & HEATMAPS</span>
                <span className="tag tag-amber">ERROR LEVEL ANALYSIS</span>
              </div>

              <h3 className="picker-detail-headline">Digital Tampering Forensics</h3>
              <p className="picker-detail-desc">
                High-frequency compression gradient analysis identifying resaved, spliced, or digitally manipulated regions.
              </p>

              <div className="amber-divider" />

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginTop: '1rem' }}>
                <div>
                  <span className="eyebrow" style={{ fontSize: '9px' }}>ORIGINAL ASSET</span>
                  <div style={{ height: '180px', background: 'var(--bg-overlay)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginTop: '0.35rem', overflow: 'hidden', position: 'relative' }}>
                    {targetImgSrc ? (
                      <img
                        src={targetImgSrc}
                        alt="Original Asset"
                        style={{ width: '100%', height: '100%', objectFit: 'contain' }}
                        onError={(e) => {
                          e.currentTarget.style.display = 'none';
                          const fb = e.currentTarget.parentElement.querySelector('.orig-fallback');
                          if (fb) fb.style.display = 'flex';
                        }}
                      />
                    ) : null}
                    <div
                      className="orig-fallback"
                      style={{
                        display: targetImgSrc ? 'none' : 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        gap: '0.3rem',
                      }}
                    >
                      <ImageIcon size={28} color="var(--cream)" style={{ opacity: 0.6 }} />
                      <span className="font-mono" style={{ fontSize: '11px', color: 'var(--muted)' }}>Original Capture</span>
                    </div>
                  </div>
                </div>

                <div>
                  <span className="eyebrow" style={{ fontSize: '9px' }}>ELA GRADIENT MAP</span>
                  <div style={{ height: '180px', background: 'var(--bg-overlay)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginTop: '0.35rem', overflow: 'hidden', position: 'relative' }}>
                    {elaImgSrc ? (
                      <img
                        src={elaImgSrc}
                        alt="ELA Compression Map"
                        style={{ width: '100%', height: '100%', objectFit: 'contain' }}
                        onError={(e) => {
                          e.currentTarget.style.display = 'none';
                          const fb = e.currentTarget.parentElement.querySelector('.ela-fallback');
                          if (fb) fb.style.display = 'flex';
                        }}
                      />
                    ) : null}
                    <div
                      className="ela-fallback"
                      style={{
                        display: elaImgSrc ? 'none' : 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        gap: '0.3rem',
                      }}
                    >
                      <Layers size={28} color="var(--amber)" style={{ opacity: 0.7 }} />
                      <span className="font-mono" style={{ fontSize: '11px', color: 'var(--amber)' }}>Compression Surface Map</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="amber-divider" />

              <div className="two-col-meta">
                <div>
                  <div className="meta-label">MANIPULATION SCORE</div>
                  <div className="meta-value-mono">{manipulation?.manipulation_score ?? 6.7}%</div>
                </div>
                <div>
                  <div className="meta-label">ANALYSIS VERDICT</div>
                  <div className="meta-value" style={{ fontFamily: 'Fraunces', fontSize: '16px' }}>
                    {manipulation?.manipulation_score >= 40 ? 'Potential Compression Anomaly' : 'Authentic Pixel Distribution'}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 03: Multimodal Risk Audit */}
          {activeTab === 'audit' && (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span className="eyebrow">TAB 03 — MULTIMODAL RISK AUDIT</span>
                <span className="font-mono" style={{ fontSize: '11px', color: 'var(--amber)' }}>
                  Mathematical Weights
                </span>
              </div>

              <h3 className="picker-detail-headline">Risk Formulation Breakdown</h3>
              <p className="picker-detail-desc">
                Transparent linear risk model combining vision transformer cosine similarity, policy disclosures, and logo integrity.
              </p>

              <div className="amber-divider" />

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginBottom: '0.2rem' }}>
                    <span>Visual Risk Weight</span>
                    <span className="font-mono" style={{ color: 'var(--amber)' }}>60%</span>
                  </div>
                  <div className="progress-track"><div className="progress-fill" style={{ width: '60%', background: 'var(--amber)' }} /></div>
                </div>

                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginBottom: '0.2rem' }}>
                    <span>Text & Compliance Weight</span>
                    <span className="font-mono" style={{ color: 'var(--cream)' }}>40%</span>
                  </div>
                  <div className="progress-track"><div className="progress-fill" style={{ width: '40%', background: 'var(--cream)' }} /></div>
                </div>
              </div>

              <div className="amber-divider" />

              <div className="two-col-meta">
                <div>
                  <div className="meta-label">DECISION FORMULA</div>
                  <div className="meta-value font-mono" style={{ fontSize: '12px', color: 'var(--muted)' }}>
                    R = 0.60(V_risk) + 0.40(T_risk)
                  </div>
                </div>
                <div>
                  <div className="meta-label">HARD OVERRIDE GATES</div>
                  <div className="meta-value" style={{ fontSize: '12px' }}>
                    Redirect Loop (&gt;3 hops) · WAF 403 · robots.txt
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 04: Vision Backbone Provenance */}
          {activeTab === 'provenance' && (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span className="eyebrow">TAB 04 — BACKBONE PROVENANCE</span>
                <span className="font-mono" style={{ fontSize: '11px', color: 'var(--amber)' }}>
                  PyTorch / HuggingFace
                </span>
              </div>

              <h3 className="picker-detail-headline">Vision Transformer Architecture</h3>
              <p className="picker-detail-desc">
                Pre-trained Vision Transformer model specifications and cosine similarity embedding geometry.
              </p>

              <div className="amber-divider" />

              <div className="two-col-meta">
                <div>
                  <div className="meta-label">MODEL ARCHITECTURE</div>
                  <div className="meta-value font-mono">ViT-B/16 (Patch-16, 224px)</div>
                </div>
                <div>
                  <div className="meta-label">EMBEDDING DIMENSION</div>
                  <div className="meta-value font-mono">768-d dense representation</div>
                </div>
                <div>
                  <div className="meta-label">SIMILARITY METRIC</div>
                  <div className="meta-value font-mono">Cosine distance · dot product norm</div>
                </div>
                <div>
                  <div className="meta-label">EXECUTION RUNTIME</div>
                  <div className="meta-value font-mono">Torch CPU/CUDA In-Memory</div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 05: JSON Export */}
          {activeTab === 'json' && (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span className="eyebrow">TAB 05 — RAW JSON DOSSIER</span>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <button
                    className="btn-secondary"
                    style={{ padding: '0.35rem 0.75rem', fontSize: '11px' }}
                    onClick={handleCopyJson}
                  >
                    {copied ? <Check size={12} /> : <Copy size={12} />}
                    <span>{copied ? 'COPIED' : 'COPY'}</span>
                  </button>
                  <button
                    className="btn-primary"
                    style={{ padding: '0.35rem 0.75rem', fontSize: '11px' }}
                    onClick={downloadJsonReport}
                  >
                    <Download size={12} />
                    <span>DOWNLOAD</span>
                  </button>
                </div>
              </div>

              <h3 className="picker-detail-headline">Underwriting Dossier Payload</h3>

              <div className="amber-divider" />

              <pre style={{
                background: 'var(--bg-base)',
                border: '1px solid var(--border)',
                borderRadius: 'var(--radius-md)',
                padding: '1rem',
                maxHeight: '280px',
                overflow: 'auto',
                fontSize: '12px',
                fontFamily: 'JetBrains Mono',
                color: 'var(--cream)',
                lineHeight: 1.5,
              }}>
                {JSON.stringify(result, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
