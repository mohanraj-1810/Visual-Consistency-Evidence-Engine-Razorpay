import React from 'react';
import { Eye, Globe, Database, ShieldCheck, ShieldAlert, Sparkles, Image as ImageIcon } from 'lucide-react';
import { formatImageSrc } from '../utils/imageHelper';

export default function EvidenceFusionCards({ evidence = [] }) {
  if (!Array.isArray(evidence) || evidence.length === 0) return null;

  return (
    <div style={{ marginBottom: '1.5rem' }}>
      {/* ── 3-Column Evidence Fusion Grid (Screen 5) ── */}
      <div className="evidence-grid">
        {evidence.map((item, idx) => {
          if (!item || typeof item !== 'object') return null;

          const webScore = item.google_web_match_score ?? item.web_match_score ?? 0;
          const vitScore = item.local_vit_similarity_score ?? Math.round((item.vit_cosine_similarity ?? item.similarity ?? 0) * 100);
          const corroborated = Boolean(item.corroborated) || webScore >= 70 || vitScore >= 70;
          const isPotentialReuse = webScore >= 40 || vitScore >= 40;
          const matchedDomains = Array.isArray(item.matched_domains) ? item.matched_domains : item.source_domain ? [item.source_domain] : [];

          const numStr = String(idx + 1).padStart(2, '0');
          const imgSrc = formatImageSrc(
            item.image_base64 ||
            item.asset_image_base64 ||
            item.matched_image_base64 ||
            item.base64 ||
            item.asset_url ||
            item.image_url ||
            item.src
          );

          return (
            <div
              key={idx}
              className={`exhibit-card ${corroborated ? 'flagged' : ''}`}
            >
              {/* Header */}
              <div className="exhibit-card-header">
                <span className="eyebrow">EXHIBIT {numStr}</span>
                {corroborated ? (
                  <span className="tag tag-amber">⚑ REUSE DETECTED</span>
                ) : isPotentialReuse ? (
                  <span className="tag tag-amber">POTENTIAL MATCH</span>
                ) : (
                  <span className="tag tag-green">UNIQUE ASSET</span>
                )}
              </div>

              {/* Thumbnail Area */}
              <div className="exhibit-thumb" style={{ position: 'relative', overflow: 'hidden' }}>
                {imgSrc ? (
                  <img
                    src={imgSrc}
                    alt={`Exhibit ${numStr}`}
                    style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                    onError={(e) => {
                      e.currentTarget.style.display = 'none';
                      const fb = e.currentTarget.parentElement.querySelector('.fallback-placeholder');
                      if (fb) fb.style.display = 'flex';
                    }}
                  />
                ) : null}

                <div
                  className="fallback-placeholder"
                  style={{
                    display: imgSrc ? 'none' : 'flex',
                    width: '100%',
                    height: '100%',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '0.4rem',
                    background: 'radial-gradient(ellipse at center, rgba(217,161,92,0.06) 0%, rgba(23,21,18,0.95) 100%)',
                  }}
                >
                  <ImageIcon size={28} color="var(--amber)" style={{ opacity: 0.7 }} />
                  <span className="font-mono" style={{ fontSize: '11px', color: 'var(--cream)', opacity: 0.85 }}>
                    {item.asset_type || 'storefront_image'}
                  </span>
                  <span className="font-mono" style={{ fontSize: '9px', color: 'var(--muted)' }}>
                    {item.sha256 ? `hash:${item.sha256.slice(0, 10)}...` : 'Visual Fingerprint Verified'}
                  </span>
                </div>
              </div>

              {/* Stats Row (Web Match vs Platform ViT) */}
              <div className="exhibit-stats">
                <div className="exhibit-stat">
                  <span className="eyebrow" style={{ fontSize: '9px' }}>WEB MATCH</span>
                  <span
                    className={`exhibit-stat-pct ${webScore >= 70 ? 'warning' : webScore >= 40 ? 'caution' : 'clear'}`}
                  >
                    {webScore}%
                  </span>
                  <span style={{ fontSize: '10px', color: 'var(--muted)', textTransform: 'capitalize' }}>
                    {item.provider_result ? String(item.provider_result).replace('_', ' ') : 'search index'}
                  </span>
                </div>

                <div className="exhibit-stat-divider" />

                <div className="exhibit-stat">
                  <span className="eyebrow" style={{ fontSize: '9px' }}>PLATFORM VIT %</span>
                  <span
                    className={`exhibit-stat-pct ${vitScore >= 70 ? 'warning' : vitScore >= 40 ? 'caution' : 'clear'}`}
                  >
                    {vitScore}%
                  </span>
                  <span className="font-mono" style={{ fontSize: '10px', color: 'var(--muted)' }}>
                    cos {item.vit_cosine_similarity ?? (vitScore / 100).toFixed(2)}
                  </span>
                </div>
              </div>

              {/* Footer details: matched domain or explanation */}
              {(matchedDomains.length > 0 || item.explanation) && (
                <div style={{ padding: '0 1rem 0.85rem', borderTop: '1px solid var(--border)', paddingTop: '0.65rem', fontSize: '12px' }}>
                  {matchedDomains.length > 0 && (
                    <div style={{ color: 'var(--muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      <span style={{ color: 'var(--cream)', fontWeight: 500 }}>Matched Source:</span> {matchedDomains.join(', ')}
                    </div>
                  )}
                  {item.explanation && (
                    <div style={{ color: 'var(--muted)', marginTop: '0.25rem', lineHeight: 1.4, fontSize: '11px' }}>
                      {item.explanation}
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
