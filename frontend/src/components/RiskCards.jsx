import React from 'react';
import { AlertTriangle, CheckCircle2, ShieldCheck, HelpCircle, Layers, ShieldAlert, FileText, WifiOff } from 'lucide-react';

export default function RiskCards({ fusion, claims, webDetectionMode, webDetectionSimulated }) {
  if (!fusion) return null;

  const isComplianceLimited = fusion.status === 'COMPLIANCE_LIMITED' || fusion.is_compliance_limited;
  const isBotBlocked = fusion.status === 'BOT_BLOCKED' || fusion.is_bot_blocked;
  const isUnverifiable = (fusion.status === 'UNVERIFIABLE' || fusion.is_unverifiable || fusion.final_risk_score === null) && !isComplianceLimited && !isBotBlocked;
  const textScore = fusion.text_risk_score;
  const visualScore = fusion.visual_risk_score;
  const finalScore = fusion.final_risk_score;
  const status = fusion.status ?? (isComplianceLimited ? 'COMPLIANCE_LIMITED' : isBotBlocked ? 'BOT_BLOCKED' : isUnverifiable ? 'UNVERIFIABLE' : 'LOW');
  const statusLabel = fusion.status_label ?? (isComplianceLimited ? 'COMPLIANCE-LIMITED — ACCESS RESTRICTED PER POLICY' : isBotBlocked ? 'COULD NOT VERIFY — ANTI-BOT PROTECTION (HTTP 403)' : isUnverifiable ? 'UNVERIFIABLE — INSUFFICIENT EVIDENCE' : 'LOW — NORMAL ONBOARDING');
  const recommendation = fusion.recommendation ?? 'Merchant exhibits normal risk parameters.';
  const badgeColor = fusion.badge_color ?? (isComplianceLimited ? '#2563eb' : isBotBlocked ? '#6366f1' : isUnverifiable ? '#64748b' : '#10b981');

  // Dynamic colors
  const visualColor = isComplianceLimited ? '#60a5fa' : isBotBlocked ? '#818cf8' : isUnverifiable ? '#94a3b8' : visualScore >= 70 ? '#ef4444' : visualScore >= 40 ? '#f59e0b' : '#10b981';
  const finalColor = badgeColor;

  return (
    <div style={{ marginBottom: '2.5rem' }}>
      {/* ── BOT_BLOCKED WAF / anti-bot notice banner ── */}
      {isBotBlocked && (
        <div
          style={{
            display: 'flex',
            alignItems: 'flex-start',
            gap: '0.75rem',
            background: 'rgba(99, 102, 241, 0.12)',
            border: '1.5px solid #6366f1',
            borderRadius: '10px',
            padding: '0.85rem 1.15rem',
            marginBottom: '1.25rem',
          }}
        >
          <ShieldAlert size={20} color="#818cf8" style={{ flexShrink: 0, marginTop: '2px' }} />
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.2rem' }}>
              <span
                style={{
                  background: '#6366f1',
                  color: '#ffffff',
                  fontWeight: 800,
                  fontSize: '0.72rem',
                  letterSpacing: '0.06em',
                  padding: '0.15rem 0.5rem',
                  borderRadius: '4px',
                  textTransform: 'uppercase',
                }}
              >
                ANTI-BOT PROTECTED
              </span>
              <strong style={{ color: '#c7d2fe', fontSize: '0.9rem' }}>
                COULD NOT VERIFY — Target Site's Anti-Bot Protection Blocked Automated Access (HTTP 403)
              </strong>
            </div>
            <p style={{ color: '#e0e7ff', fontSize: '0.82rem', margin: 0, lineHeight: 1.4 }}>
              Target site's anti-bot protection (Cloudflare / PerimeterX / WAF) blocked automated scraper access (HTTP 403). This does not indicate risk — many large legitimate platforms (Etsy, Amazon, etc.) block automated crawlers by design.
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
            gap: '0.75rem',
            background: 'rgba(37, 99, 235, 0.12)',
            border: '1.5px solid #3b82f6',
            borderRadius: '10px',
            padding: '0.85rem 1.15rem',
            marginBottom: '1.25rem',
          }}
        >
          <ShieldCheck size={20} color="#3b82f6" style={{ flexShrink: 0, marginTop: '2px' }} />
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.2rem' }}>
              <span
                style={{
                  background: '#2563eb',
                  color: '#ffffff',
                  fontWeight: 800,
                  fontSize: '0.72rem',
                  letterSpacing: '0.06em',
                  padding: '0.15rem 0.5rem',
                  borderRadius: '4px',
                  textTransform: 'uppercase',
                }}
              >
                COMPLIANCE-LIMITED
              </span>
              <strong style={{ color: '#93c5fd', fontSize: '0.9rem' }}>
                Automated Bot Access Disallowed by robots.txt (Site is Live & Compliant)
              </strong>
            </div>
            <p style={{ color: '#bfdbfe', fontSize: '0.82rem', margin: 0, lineHeight: 1.4 }}>
              Robots.txt disallows automated crawler access to this page. The site is active and policy-compliant, but automated visual extraction was suspended per web standards. No negative risk inference.
            </p>
          </div>
        </div>
      )}

      {/* ── UNVERIFIABLE crawl failure notice banner (DNS / Network failures only) ── */}
      {isUnverifiable && (
        <div
          style={{
            display: 'flex',
            alignItems: 'flex-start',
            gap: '0.75rem',
            background: 'rgba(100, 116, 139, 0.15)',
            border: '1.5px solid #64748b',
            borderRadius: '10px',
            padding: '0.85rem 1.15rem',
            marginBottom: '1.25rem',
          }}
        >
          <AlertTriangle size={20} color="#94a3b8" style={{ flexShrink: 0, marginTop: '2px' }} />
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.2rem' }}>
              <span
                style={{
                  background: '#64748b',
                  color: '#f8fafc',
                  fontWeight: 800,
                  fontSize: '0.72rem',
                  letterSpacing: '0.06em',
                  padding: '0.15rem 0.5rem',
                  borderRadius: '4px',
                  textTransform: 'uppercase',
                }}
              >
                UNVERIFIABLE
              </span>
              <strong style={{ color: '#f1f5f9', fontSize: '0.9rem' }}>
                Automated Visual Risk Scoring Suspended — Site Unreachable
              </strong>
            </div>
            <p style={{ color: '#cbd5e1', fontSize: '0.82rem', margin: 0, lineHeight: 1.4 }}>
              {fusion.crawl_error || 'The merchant domain could not be resolved or reached via HTTP/DNS. Automated risk signals were suspended to prevent false auto-approvals.'}
            </p>
          </div>
        </div>
      )}

      {/* ── SIMULATED / DEMO MODE banner ── framed positively as intentional demo configuration */}
      {webDetectionSimulated && (
        <div
          style={{
            display: 'flex',
            alignItems: 'flex-start',
            gap: '0.75rem',
            background: 'rgba(245, 158, 11, 0.10)',
            border: '1.5px solid #f59e0b',
            borderRadius: '10px',
            padding: '0.85rem 1.15rem',
            marginBottom: '1.25rem',
          }}
        >
          <WifiOff size={20} color="#f59e0b" style={{ flexShrink: 0, marginTop: '2px' }} />
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.2rem' }}>
              <span
                style={{
                  background: '#f59e0b',
                  color: '#0f172a',
                  fontWeight: 800,
                  fontSize: '0.72rem',
                  letterSpacing: '0.06em',
                  padding: '0.15rem 0.5rem',
                  borderRadius: '4px',
                  textTransform: 'uppercase',
                }}
              >
                DEMO MODE
              </span>
              <strong style={{ color: '#fcd34d', fontSize: '0.9rem' }}>
                Reverse image search: DEMO MODE
              </strong>
            </div>
            <p style={{ color: '#cbd5e1', fontSize: '0.82rem', margin: 0, lineHeight: 1.4 }}>
              This environment runs without live Google Cloud Vision credentials. In production, this stage performs real reverse-image web search via the Vision API to detect stolen or reused product photos across the open web.
            </p>
          </div>
        </div>
      )}

      {/* Merchant Overview Header Card */}
      <div
        style={{
          background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
          border: `1px solid ${isUnverifiable ? '#475569' : '#334155'}`,
          borderRadius: '12px',
          padding: '1.25rem 1.5rem',
          marginBottom: '1.25rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
        }}
      >
        <div>
          <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#94a3b8', fontWeight: 600 }}>
            Merchant Entity Under Review
          </div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#f8fafc', margin: '0.15rem 0' }}>
            {fusion.merchant_name}
          </h2>
          {claims?.inventory_claim && (
            <div style={{ fontSize: '0.85rem', color: '#cbd5e1', fontStyle: 'italic', maxWidth: '650px' }}>
              Claim: "{claims.inventory_claim}"
            </div>
          )}
        </div>

        <div style={{ textAlign: 'right' }}>
          <span
            className="status-badge"
            style={{
              backgroundColor: finalColor,
              fontSize: '0.9rem',
              padding: '0.5rem 1.1rem',
              letterSpacing: '0.04em',
              fontWeight: 800,
            }}
          >
            {statusLabel}
          </span>
          <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '0.4rem' }}>
            Explainable Decision Support Metric
          </div>
        </div>
      </div>

      {/* 4 Score Summary Cards */}
      <div className="risk-cards-grid">
        {/* Card 1: Text Risk */}
        <div className="risk-card">
          <div className="risk-card-header">
            <span style={{ color: '#94a3b8' }}>Merchant Compliance Disclosures</span>
          </div>
          <div>
            <div className="risk-score-value" style={{ color: isUnverifiable ? '#94a3b8' : '#60a5fa' }}>
              {isUnverifiable || textScore === null ? 'N/A' : textScore}{' '}
              {!isUnverifiable && textScore !== null && <span className="risk-score-denom">/ 100</span>}
            </div>
            <div className="risk-card-footer">Website Disclosures & Contact Info</div>
          </div>
          <div style={{ fontSize: '0.72rem', color: '#64748b', marginTop: '0.4rem' }}>
            {isUnverifiable ? 'Unverifiable due to unreachable host' : 'Standard merchant disclosures & policies'}
          </div>
        </div>

        {/* Card 2: Visual Evidence Risk */}
        <div className="risk-card">
          <div className="risk-card-header">
            <span>Visual Evidence Risk</span>
          </div>
          <div>
            <div className="risk-score-value" style={{ color: visualColor }}>
              {isUnverifiable || visualScore === null ? 'N/A' : visualScore}{' '}
              {!isUnverifiable && visualScore !== null && <span className="risk-score-denom">/ 100</span>}
            </div>
            <div className="risk-card-footer">ViT & Multi-Signal Visual Forensics</div>
          </div>
          <div style={{ fontSize: '0.72rem', color: '#64748b', marginTop: '0.4rem' }}>
            {isUnverifiable ? 'No visual assets retrieved' : 'Reuse, tampering, logo variance, coherence'}
          </div>
        </div>

        {/* Card 3: Final Fused Risk */}
        <div className="risk-card" style={{ border: `2px solid ${finalColor}`, background: 'rgba(15, 23, 42, 0.95)' }}>
          <div className="risk-card-header" style={{ color: '#f8fafc', fontWeight: 800 }}>
            Final Fused Risk Score
          </div>
          <div>
            <div className="risk-score-value" style={{ color: finalColor }}>
              {isUnverifiable || finalScore === null ? 'N/A' : finalScore}{' '}
              {!isUnverifiable && finalScore !== null && <span className="risk-score-denom">/ 100</span>}
            </div>
            <div className="risk-card-footer" style={{ color: '#e2e8f0', fontWeight: 700 }}>
              {isUnverifiable ? 'Suspended (Insufficient Evidence)' : 'Evidence-Weighted Multimodal Fusion'}
            </div>
          </div>
          <div style={{ fontSize: '0.72rem', color: '#94a3b8', marginTop: '0.4rem' }}>
            {isUnverifiable ? 'Cannot compute score on dead site' : 'Visual contradictions override text facade'}
          </div>
        </div>

        {/* Card 4: Classification & Action */}
        <div className="risk-card" style={{ justifyContent: 'center', background: '#0f172a' }}>
          <div className="risk-card-header">Review Action</div>
          <div style={{ margin: '0.4rem 0' }}>
            <span
              style={{
                display: 'inline-block',
                padding: '0.35rem 0.75rem',
                borderRadius: '6px',
                background:
                  status === 'HIGH'
                    ? 'rgba(239, 68, 68, 0.2)'
                    : status === 'MEDIUM'
                    ? 'rgba(245, 158, 11, 0.2)'
                    : status === 'COMPLIANCE_LIMITED'
                    ? 'rgba(37, 99, 235, 0.2)'
                    : status === 'BOT_BLOCKED'
                    ? 'rgba(99, 102, 241, 0.2)'
                    : status === 'UNVERIFIABLE'
                    ? 'rgba(100, 116, 139, 0.3)'
                    : 'rgba(16, 185, 129, 0.2)',
                color: finalColor,
                fontWeight: 700,
                fontSize: '0.85rem',
                border: `1px solid ${finalColor}`,
              }}
            >
              {status === 'HIGH'
                ? '🚨 Route to Manual Review'
                : status === 'MEDIUM'
                ? '⚠️ Request Documentation'
                : status === 'COMPLIANCE_LIMITED'
                ? '🛡️ Manual Analyst Review (Policy Compliant)'
                : status === 'BOT_BLOCKED'
                ? '🔒 Manual Platform Verification (Anti-Bot WAF)'
                : status === 'UNVERIFIABLE'
                ? '❓ Manual Investigation Required (Unreachable Site)'
                : '✅ Standard Onboarding'}
            </span>
          </div>
          <div style={{ fontSize: '0.78rem', color: '#cbd5e1', lineHeight: '1.4' }}>
            {recommendation}
          </div>
        </div>
      </div>
    </div>
  );
}
