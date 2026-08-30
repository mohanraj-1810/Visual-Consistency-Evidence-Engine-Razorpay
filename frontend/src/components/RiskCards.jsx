import React from 'react';
import { AlertTriangle, ShieldCheck, ShieldAlert, FileText, ArrowRight, Download } from 'lucide-react';

export default function RiskCards({ fusion, claims, webDetectionMode, webDetectionSimulated }) {
  if (!fusion) return null;

  const isComplianceLimited = fusion.status === 'COMPLIANCE_LIMITED' || fusion.is_compliance_limited;
  const isBotBlocked = fusion.status === 'BOT_BLOCKED' || fusion.is_bot_blocked;
  const isRedirectLimitExceeded = fusion.status === 'REDIRECT_LIMIT_EXCEEDED' || fusion.is_redirect_limit_exceeded;
  const isUnverifiable = (fusion.status === 'UNVERIFIABLE' || fusion.is_unverifiable || fusion.final_risk_score === null) && !isComplianceLimited && !isBotBlocked && !isRedirectLimitExceeded;
  const isAnyUnverifiable = isUnverifiable || isComplianceLimited || isBotBlocked || isRedirectLimitExceeded;

  const textScore = fusion.text_risk_score;
  const visualScore = fusion.visual_risk_score;
  const finalScore = fusion.final_risk_score;
  const recommendation = fusion.recommendation ?? 'Merchant exhibits normal risk parameters.';

  const scoreVal = typeof finalScore === 'number' ? Math.max(0, Math.min(100, Math.round(finalScore))) : 0;

  // Determine risk category & class
  let verdictTitle = 'LOW RISK';
  let verdictClass = 'low';
  if (isRedirectLimitExceeded) {
    verdictTitle = 'REDIRECT LIMIT';
    verdictClass = 'medium';
  } else if (isBotBlocked) {
    verdictTitle = 'BOT BLOCKED';
    verdictClass = 'medium';
  } else if (isComplianceLimited) {
    verdictTitle = 'COMPLIANCE LIMITED';
    verdictClass = 'low';
  } else if (isUnverifiable) {
    verdictTitle = 'UNVERIFIABLE';
    verdictClass = 'unverifiable';
  } else if (scoreVal >= 70) {
    verdictTitle = 'HIGH RISK';
    verdictClass = 'high';
  } else if (scoreVal >= 40) {
    verdictTitle = 'MEDIUM RISK';
    verdictClass = 'medium';
  }

  // Gauge calculation: 180° arc
  const radius = 58;
  const arcLength = Math.PI * radius; // half circle perimeter
  const strokeDashoffset = arcLength - (scoreVal / 100) * arcLength;

  const gaugeStrokeColor =
    verdictClass === 'high' ? 'var(--risk-red)' :
    verdictClass === 'medium' ? 'var(--risk-amber)' :
    verdictClass === 'low' ? 'var(--risk-green)' : 'var(--muted)';

  return (
    <div style={{ marginBottom: '1.5rem' }}>
      {/* ── Status Notices for Special Cases ── */}
      {isRedirectLimitExceeded && (
        <div className="notice-banner amber-notice">
          <AlertTriangle size={18} color="var(--risk-amber)" style={{ flexShrink: 0, marginTop: '2px' }} />
          <div>
            <div className="notice-banner-title">CRAWL ABORTED — REDIRECT SAFETY LIMIT EXCEEDED</div>
            <div className="notice-banner-body">
              {fusion.crawl_error || 'Target site exceeded maximum allowable redirect limit of 3 hops (possible loop or geo barrier).'}
            </div>
          </div>
        </div>
      )}

      {isBotBlocked && (
        <div className="notice-banner amber-notice">
          <ShieldAlert size={18} color="var(--risk-amber)" style={{ flexShrink: 0, marginTop: '2px' }} />
          <div>
            <div className="notice-banner-title">ANTI-BOT ACCESS RESTRICTION (HTTP 403)</div>
            <div className="notice-banner-body">
              Target site uses WAF/Cloudflare anti-bot protection. This is standard for enterprise brands and does not imply merchant fraud.
            </div>
          </div>
        </div>
      )}

      {isComplianceLimited && (
        <div className="notice-banner">
          <ShieldCheck size={18} color="var(--risk-green)" style={{ flexShrink: 0, marginTop: '2px' }} />
          <div>
            <div className="notice-banner-title">ROBOTS.TXT COMPLIANCE LIMITATION</div>
            <div className="notice-banner-body">
              Crawler access disallowed by robots.txt. Site is policy-compliant; automated visual extraction was suspended per web standards.
            </div>
          </div>
        </div>
      )}

      {isUnverifiable && (
        <div className="notice-banner">
          <AlertTriangle size={18} color="var(--muted)" style={{ flexShrink: 0, marginTop: '2px' }} />
          <div>
            <div className="notice-banner-title">DOMAIN UNREACHABLE — SCORING SUSPENDED</div>
            <div className="notice-banner-body">
              Merchant domain could not be resolved. Scoring suspended to prevent erroneous automated decisions.
            </div>
          </div>
        </div>
      )}

      {/* ── Signature Verdict Stamp Band (Screen 3) ── */}
      <div className="verdict-stamp">
        {/* Left: Metadata */}
        <div>
          <span className="eyebrow">FINAL DETERMINATION</span>
          <div style={{ fontFamily: 'Fraunces', fontSize: '20px', color: 'var(--cream)', marginTop: '0.35rem' }}>
            {fusion.merchant_name || 'Analyzed Merchant'}
          </div>
          <div className="font-mono" style={{ fontSize: '11px', color: 'var(--muted)', marginTop: '0.25rem' }}>
            {fusion.merchant_category || 'E-Commerce'} • {new Date().toLocaleTimeString()}
          </div>
        </div>

        {/* Center: Massive Serif Verdict */}
        <div style={{ textAlign: 'center' }}>
          <div className={`verdict-main ${verdictClass}`}>
            {verdictTitle}
          </div>
          <div className="eyebrow" style={{ marginTop: '0.35rem', color: 'var(--muted)' }}>
            {fusion.status_label || (isAnyUnverifiable ? 'SPECIAL POLICY STATUS' : 'MULTIMODAL RISK VERDICT')}
          </div>
        </div>

        {/* Right: Action Pills */}
        <div className="verdict-actions">
          <button
            className="btn-primary"
            onClick={() => window.alert('Dossier queued for human risk analyst review.')}
          >
            REQUEST HUMAN REVIEW
          </button>
          <button
            className="btn-secondary"
            onClick={() => {
              const blob = new Blob([JSON.stringify(fusion, null, 2)], { type: 'application/json' });
              const url = URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.href = url;
              a.download = `risk-dossier-${fusion.merchant_name || 'merchant'}.json`;
              a.click();
            }}
          >
            <Download size={13} />
            <span>EXPORT DOSSIER</span>
          </button>
        </div>
      </div>

      {/* ── Risk Score & Gauge Grid ── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr 1fr', gap: '1.25rem', marginBottom: '1.5rem', alignItems: 'stretch' }}>
        {/* Arc Gauge */}
        <div className="card" style={{ padding: '1.5rem 2rem', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minWidth: '200px' }}>
          <span className="eyebrow" style={{ marginBottom: '0.5rem' }}>COMPOSITE RISK</span>
          <div style={{ position: 'relative', width: '130px', height: '75px', overflow: 'hidden' }}>
            <svg width="130" height="130" style={{ transform: 'rotate(-180deg)', transformOrigin: '65px 65px' }}>
              <circle
                cx="65"
                cy="65"
                r={radius}
                stroke="rgba(237,227,208,0.08)"
                strokeWidth="10"
                fill="transparent"
                strokeDasharray={`${arcLength} ${arcLength}`}
                strokeLinecap="round"
              />
              <circle
                cx="65"
                cy="65"
                r={radius}
                stroke={gaugeStrokeColor}
                strokeWidth="10"
                fill="transparent"
                strokeDasharray={`${arcLength} ${arcLength}`}
                strokeDashoffset={isUnverifiable ? 0 : strokeDashoffset}
                strokeLinecap="round"
                style={{ transition: 'stroke-dashoffset 1s ease' }}
              />
            </svg>
            <div style={{ position: 'absolute', bottom: 0, left: 0, right: 0, textAlign: 'center' }}>
              <span className="risk-gauge-score">
                {isUnverifiable ? 'N/A' : scoreVal}
              </span>
            </div>
          </div>
          <span className="risk-gauge-label" style={{ marginTop: '0.35rem' }}>
            / 100 index
          </span>
        </div>

        {/* Text & Visual Component Scores */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <span className="eyebrow">COMPONENT SCORE BREAKDOWN</span>
            <div style={{ marginTop: '0.85rem', display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginBottom: '0.25rem' }}>
                  <span style={{ color: 'var(--cream)' }}>Visual Signal Dimension</span>
                  <span className="font-mono" style={{ color: 'var(--amber)', fontWeight: 600 }}>
                    {visualScore !== null && !isAnyUnverifiable ? `${visualScore}%` : 'N/A'}
                  </span>
                </div>
                <div className="progress-track">
                  <div
                    className="progress-fill"
                    style={{
                      width: `${visualScore || 0}%`,
                      background: visualScore >= 70 ? 'var(--risk-red)' : 'var(--amber)',
                    }}
                  />
                </div>
              </div>

              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginBottom: '0.25rem' }}>
                  <span style={{ color: 'var(--cream)' }}>Text & Policy Compliance</span>
                  <span className="font-mono" style={{ color: 'var(--amber)', fontWeight: 600 }}>
                    {textScore !== null && !isAnyUnverifiable ? `${textScore}%` : 'N/A'}
                  </span>
                </div>
                <div className="progress-track">
                  <div
                    className="progress-fill"
                    style={{
                      width: `${textScore || 0}%`,
                      background: textScore >= 70 ? 'var(--risk-red)' : 'var(--amber)',
                    }}
                  />
                </div>
              </div>
            </div>
          </div>
          <div className="font-mono" style={{ fontSize: '11px', color: 'var(--muted)', marginTop: '0.5rem' }}>
            Serper.dev Discovery + ViT-B/16 Cosine Engine
          </div>
        </div>

        {/* Policy Recommendation Card */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <span className="eyebrow">POLICY RECOMMENDATION</span>
            <div style={{ fontFamily: 'Fraunces', fontSize: '20px', color: 'var(--cream)', marginTop: '0.4rem', lineHeight: 1.3 }}>
              {recommendation}
            </div>
            {claims?.inventory_claim && (
              <p style={{ fontSize: '12px', color: 'var(--muted)', fontStyle: 'italic', marginTop: '0.5rem', lineHeight: 1.4 }}>
                Claim: "{claims.inventory_claim}"
              </p>
            )}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.75rem' }}>
            <span className="tag tag-amber">AUTOMATED ADVISORY</span>
            <span className="tag tag-muted">NON-BLOCKING</span>
          </div>
        </div>
      </div>
    </div>
  );
}
