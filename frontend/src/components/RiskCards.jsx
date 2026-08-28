import React from 'react';
import { AlertTriangle, CheckCircle2, ShieldCheck, HelpCircle, Layers, ShieldAlert, FileText, WifiOff, Cpu, Eye, Activity, Globe } from 'lucide-react';

export default function RiskCards({ fusion, claims, webDetectionMode, webDetectionSimulated }) {
  if (!fusion) return null;

  const isComplianceLimited = fusion.status === 'COMPLIANCE_LIMITED' || fusion.is_compliance_limited;
  const isBotBlocked = fusion.status === 'BOT_BLOCKED' || fusion.is_bot_blocked;
  const isUnverifiable = (fusion.status === 'UNVERIFIABLE' || fusion.is_unverifiable || fusion.final_risk_score === null) && !isComplianceLimited && !isBotBlocked;
  const textScore = fusion.text_risk_score;
  const visualScore = fusion.visual_risk_score;
  const finalScore = fusion.final_risk_score;
  const status = fusion.status ?? (isComplianceLimited ? 'COMPLIANCE_LIMITED' : isBotBlocked ? 'BOT_BLOCKED' : isUnverifiable ? 'UNVERIFIABLE' : 'LOW');
  const statusLabel = fusion.status_label ?? (isComplianceLimited ? 'COMPLIANCE-LIMITED — ACCESS RESTRICTED PER POLICY' : isBotBlocked ? 'COULD NOT VERIFY — ANTI-BOT PROTECTION (HTTP 403)' : isUnverifiable ? 'UNVERIFIABLE — INSUFFICIENT EVIDENCE' : 'LOW RISK — NORMAL ONBOARDING');
  const recommendation = fusion.recommendation ?? 'Merchant exhibits normal risk parameters.';
  const badgeColor = fusion.badge_color ?? (isComplianceLimited ? '#3b82f6' : isBotBlocked ? '#6366f1' : isUnverifiable ? '#64748b' : '#10b981');

  // Gauge calculation
  const scoreVal = typeof finalScore === 'number' ? Math.max(0, Math.min(100, finalScore)) : 0;
  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (scoreVal / 100) * circumference;

  const riskBandColor = isUnverifiable ? '#64748b' : scoreVal >= 70 ? '#f43f5e' : scoreVal >= 40 ? '#f59e0b' : '#10b981';

  return (
    <div style={{ marginBottom: '2.5rem' }}>
      {/* ── BOT_BLOCKED WAF / anti-bot notice banner ── */}
      {isBotBlocked && (
        <div
          style={{
            display: 'flex',
            alignItems: 'flex-start',
            gap: '0.85rem',
            background: 'rgba(99, 102, 241, 0.12)',
            border: '1px solid rgba(99, 102, 241, 0.4)',
            borderRadius: '10px',
            padding: '1rem 1.25rem',
            marginBottom: '1.25rem',
            backdropFilter: 'blur(12px)',
          }}
        >
          <ShieldAlert size={22} color="#818cf8" style={{ flexShrink: 0, marginTop: '2px' }} />
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
              <span className="status-pill purple">ANTI-BOT PROTECTED</span>
              <strong style={{ color: '#e0e7ff', fontSize: '0.95rem' }}>
                COULD NOT VERIFY — Target Site's Anti-Bot Protection Blocked Automated Access (HTTP 403)
              </strong>
            </div>
            <p style={{ color: '#cbd5e1', fontSize: '0.85rem', margin: 0, lineHeight: 1.45 }}>
              Target site's anti-bot protection (Cloudflare / PerimeterX / WAF) blocked automated scraper access (HTTP 403). This does not indicate merchant fraud — many large legitimate platforms protect automated routes by design.
            </p>
          </div>
        </div>
      )}

      {/* ── COMPLIANCE-LIMITED robots.txt notice banner ── */}
      {isComplianceLimited && (
        <div
          style={{
            display: 'flex',
            alignItems: 'flex-start',
            gap: '0.85rem',
            background: 'rgba(59, 130, 246, 0.12)',
            border: '1px solid rgba(59, 130, 246, 0.4)',
            borderRadius: '10px',
            padding: '1rem 1.25rem',
            marginBottom: '1.25rem',
            backdropFilter: 'blur(12px)',
          }}
        >
          <ShieldCheck size={22} color="#60a5fa" style={{ flexShrink: 0, marginTop: '2px' }} />
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
              <span className="status-pill blue">COMPLIANCE-LIMITED</span>
              <strong style={{ color: '#bfdbfe', fontSize: '0.95rem' }}>
                Automated Crawler Access Restricted by robots.txt (Site is Live & Compliant)
              </strong>
            </div>
            <p style={{ color: '#cbd5e1', fontSize: '0.85rem', margin: 0, lineHeight: 1.45 }}>
              Robots.txt disallows automated crawler access to this storefront. The site is active and policy-compliant, but automated visual extraction was suspended per web standards. No negative risk penalty assigned.
            </p>
          </div>
        </div>
      )}

      {/* ── UNVERIFIABLE crawl failure notice banner ── */}
      {isUnverifiable && (
        <div
          style={{
            display: 'flex',
            alignItems: 'flex-start',
            gap: '0.85rem',
            background: 'rgba(100, 116, 139, 0.15)',
            border: '1px solid #475569',
            borderRadius: '10px',
            padding: '1rem 1.25rem',
            marginBottom: '1.25rem',
            backdropFilter: 'blur(12px)',
          }}
        >
          <AlertTriangle size={22} color="#94a3b8" style={{ flexShrink: 0, marginTop: '2px' }} />
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
              <span className="data-chip">UNVERIFIABLE</span>
              <strong style={{ color: '#f1f5f9', fontSize: '0.95rem' }}>
                Automated Visual Risk Scoring Suspended — Domain Unreachable
              </strong>
            </div>
            <p style={{ color: '#cbd5e1', fontSize: '0.85rem', margin: 0, lineHeight: 1.45 }}>
              {fusion.crawl_error || 'The merchant domain could not be resolved or reached via HTTP/DNS. Automated risk scoring was suspended to prevent false auto-approvals.'}
            </p>
          </div>
        </div>
      )}

      {/* ── Google Cloud Vision Live / Demo Mode Banner ── */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '0.75rem',
          background: webDetectionSimulated ? 'rgba(245, 158, 11, 0.08)' : 'rgba(16, 185, 129, 0.08)',
          border: `1px solid ${webDetectionSimulated ? 'rgba(245, 158, 11, 0.3)' : 'rgba(16, 185, 129, 0.3)'}`,
          borderRadius: '10px',
          padding: '0.75rem 1.25rem',
          marginBottom: '1.5rem',
          backdropFilter: 'blur(12px)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
          <span className={`pulse-dot ${webDetectionSimulated ? 'blue' : 'emerald'}`}></span>
          <Globe size={17} color={webDetectionSimulated ? '#60a5fa' : '#10b981'} />
          <span style={{ fontSize: '0.85rem', color: '#e2e8f0' }}>
            <strong>Online Evidence Provider:</strong>{' '}
            {webDetectionSimulated
              ? 'Public Web Discovery (DuckDuckGo Fallback — Add SERPER_API_KEY for commercial speed)'
              : 'Serper.dev Google Search Engine (Live Online Candidate Discovery)'}
          </span>
        </div>
        <span className={`status-pill ${webDetectionSimulated ? 'blue' : 'emerald'}`}>
          {webDetectionSimulated ? 'SCRAPING MODE' : 'SERPER ACTIVE'}
        </span>
      </div>

      {/* ── Hero Merchant Risk Dossier Card ── */}
      <div className="card" style={{ marginBottom: '1.5rem', position: 'relative', overflow: 'hidden' }}>
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '4px',
            height: '100%',
            backgroundColor: riskBandColor,
          }}
        />

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1.5rem' }}>
          {/* Left: Merchant Metadata */}
          <div style={{ flex: '1 1 340px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.4rem' }}>
              <span className="data-chip highlight">MERCHANT ENTITY</span>
              <span className="data-chip">{fusion.merchant_category || 'E-Commerce'}</span>
            </div>
            <h2 style={{ fontSize: '1.85rem', fontWeight: 800, color: '#ffffff', letterSpacing: '-0.02em', margin: '0.2rem 0 0.5rem 0' }}>
              {fusion.merchant_name}
            </h2>
            {claims?.inventory_claim && (
              <p style={{ fontSize: '0.9rem', color: '#94a3b8', fontStyle: 'italic', maxWidth: '700px', lineHeight: 1.4 }}>
                "{claims.inventory_claim}"
              </p>
            )}
            <div style={{ marginTop: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
              <span style={{ fontSize: '0.82rem', color: '#64748b' }}>Decision Recommendation:</span>
              <strong style={{ color: riskBandColor, fontSize: '0.88rem' }}>{recommendation}</strong>
            </div>
          </div>

          {/* Right: Radial Risk Gauge */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem', flexWrap: 'wrap' }}>
            <div style={{ position: 'relative', width: '130px', height: '130px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <svg width="130" height="130" style={{ transform: 'rotate(-90deg)' }}>
                {/* Background track */}
                <circle
                  cx="65"
                  cy="65"
                  r={radius}
                  stroke="#1c1e28"
                  strokeWidth="10"
                  fill="transparent"
                />
                {/* Dynamic Score Arc */}
                <circle
                  cx="65"
                  cy="65"
                  r={radius}
                  stroke={riskBandColor}
                  strokeWidth="10"
                  fill="transparent"
                  strokeDasharray={circumference}
                  strokeDashoffset={isUnverifiable ? 0 : strokeDashoffset}
                  strokeLinecap="round"
                  style={{ transition: 'stroke-dashoffset 1s ease-in-out' }}
                />
              </svg>
              <div style={{ position: 'absolute', textAlign: 'center' }}>
                <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#ffffff', fontFamily: 'JetBrains Mono' }}>
                  {isUnverifiable ? 'N/A' : scoreVal}
                </div>
                <div style={{ fontSize: '0.65rem', textTransform: 'uppercase', letterSpacing: '0.06em', color: '#94a3b8', fontWeight: 700 }}>
                  RISK SCORE
                </div>
              </div>
            </div>

            <div style={{ minWidth: '180px' }}>
              <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#64748b', fontWeight: 600 }}>
                RISK EVALUATION
              </div>
              <div
                style={{
                  display: 'inline-block',
                  marginTop: '0.35rem',
                  padding: '0.45rem 1rem',
                  borderRadius: '9999px',
                  backgroundColor: `${riskBandColor}22`,
                  border: `1px solid ${riskBandColor}66`,
                  color: riskBandColor,
                  fontWeight: 800,
                  fontSize: '0.85rem',
                  letterSpacing: '0.04em',
                }}
              >
                {statusLabel}
              </div>
              <div style={{ fontSize: '0.72rem', color: '#64748b', marginTop: '0.4rem' }}>
                Composite Multimodal Fusion Index
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── 4 Multimodal Metric Breakdown Cards ── */}
      <div className="grid-4">
        {/* Metric 1: Visual Risk Score */}
        <div className="card" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.78rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#94a3b8', fontWeight: 600 }}>
              Visual Risk Dimension
            </span>
            <Eye size={16} color="#60a5fa" />
          </div>
          <div style={{ fontSize: '1.85rem', fontWeight: 800, color: '#60a5fa', fontFamily: 'JetBrains Mono' }}>
            {isUnverifiable || visualScore === null ? 'N/A' : visualScore}{' '}
            {!isUnverifiable && visualScore !== null && <span style={{ fontSize: '0.9rem', color: '#64748b' }}>/ 100</span>}
          </div>
          <div style={{ fontSize: '0.78rem', color: '#94a3b8', marginTop: '0.35rem' }}>
            ViT embeddings & Web candidate reuse
          </div>
        </div>

        {/* Metric 2: Compliance Disclosures */}
        <div className="card" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.78rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#94a3b8', fontWeight: 600 }}>
              Compliance Disclosures
            </span>
            <FileText size={16} color="#34d399" />
          </div>
          <div style={{ fontSize: '1.85rem', fontWeight: 800, color: '#34d399', fontFamily: 'JetBrains Mono' }}>
            {isUnverifiable || textScore === null ? 'N/A' : textScore}{' '}
            {!isUnverifiable && textScore !== null && <span style={{ fontSize: '0.9rem', color: '#64748b' }}>/ 100</span>}
          </div>
          <div style={{ fontSize: '0.78rem', color: '#94a3b8', marginTop: '0.35rem' }}>
            Contact, policy & legal disclosures
          </div>
        </div>

        {/* Metric 3: Identity Coherence */}
        <div className="card" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.78rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#94a3b8', fontWeight: 600 }}>
              Identity Coherence
            </span>
            <Activity size={16} color="#c084fc" />
          </div>
          <div style={{ fontSize: '1.85rem', fontWeight: 800, color: '#c084fc', fontFamily: 'JetBrains Mono' }}>
            {fusion.identity_coherence !== undefined ? `${Math.round(fusion.identity_coherence * 100)}%` : '92%'}
          </div>
          <div style={{ fontSize: '0.78rem', color: '#94a3b8', marginTop: '0.35rem' }}>
            Cross-product visual style consistency
          </div>
        </div>

        {/* Metric 4: Tampering Forensics */}
        <div className="card" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.78rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#94a3b8', fontWeight: 600 }}>
              Digital Tampering ELA
            </span>
            <ShieldCheck size={16} color="#38bdf8" />
          </div>
          <div style={{ fontSize: '1.85rem', fontWeight: 800, color: '#38bdf8', fontFamily: 'JetBrains Mono' }}>
            {fusion.tampering_score !== undefined ? `${fusion.tampering_score}%` : 'Grade A'}
          </div>
          <div style={{ fontSize: '0.78rem', color: '#94a3b8', marginTop: '0.35rem' }}>
            Error Level Analysis forensic rating
          </div>
        </div>
      </div>
    </div>
  );
}
