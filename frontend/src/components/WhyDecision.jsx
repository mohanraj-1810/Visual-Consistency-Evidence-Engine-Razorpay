import React, { useState } from 'react';
import { CheckCircle2, Circle, AlertTriangle, Info, ChevronDown, ChevronUp } from 'lucide-react';

/**
 * WhyDecision — "WHY THIS DECISION?" section derived from actual pipeline outputs.
 * Shows the evidence signals that drove the risk tier, with corroboration status.
 */
export default function WhyDecision({ fusion, reuse, logo, manipulation, identity }) {
  const [expanded, setExpanded] = useState(true);

  if (!fusion) return null;

  const score = fusion.final_risk_score ?? 0;
  const tier = fusion.status_tier || fusion.status || 'CLEAR';
  const isUnverifiable = fusion.is_unverifiable || fusion.status === 'UNVERIFIABLE';

  // Build signals list from actual pipeline data
  const signals = [];

  // ── Signal 1: Image Reuse ──
  if (reuse) {
    const reuseScore = reuse.reuse_risk_score ?? 0;
    const matchStatus = reuse.match_status || 'NO_EXTERNAL_MATCH';
    const maxSim = reuse.max_similarity ?? 0;
    const srcType = reuse.top_flagged_item?.source_type || null;
    const isSupplier = srcType === 'SUPPLIER_CATALOG' || srcType === 'MARKETPLACE';

    if (maxSim > 0.3 || reuseScore > 10) {
      const isActive = reuseScore >= 70 && !isSupplier && matchStatus === 'CORROBORATED';
      const isSuppressed = isSupplier;
      const isInsufficient = matchStatus === 'INSUFFICIENT_EVIDENCE' || matchStatus === 'NO_EXTERNAL_MATCH';

      signals.push({
        id: 'image_reuse',
        label: 'Image Reuse Detection',
        detail: `ViT cosine similarity: ${Math.round(maxSim * 100)}%`,
        context: isSupplier
          ? 'Source classified as supplier/catalog — excluded from severe escalation.'
          : isInsufficient
          ? 'Single fixture match — insufficient corroboration for escalation.'
          : matchStatus === 'CORROBORATED'
          ? 'Multi-source corroborated evidence.'
          : `Evidence status: ${matchStatus.replace('_', ' ')}`,
        active: isActive,
        suppressed: isSuppressed,
        severity: isActive ? 'high' : isSupplier ? 'low' : maxSim > 0.8 ? 'medium' : 'low',
        contribution: isActive ? 'Contributed to HIGH escalation' : isSuppressed ? 'Excluded — supplier sourcing' : 'Insufficient evidence for escalation',
      });
    }
  }

  // ── Signal 2: Logo Inconsistency ──
  if (logo) {
    const logoRisk = logo.inconsistency_risk ?? 0;
    const logoSim = logo.similarity ?? 1.0;
    const matchedRef = logo.matched_reference;

    if (matchedRef || logoRisk > 15) {
      const isActive = logoRisk >= 60;
      signals.push({
        id: 'logo_divergence',
        label: 'Logo / Trademark Divergence',
        detail: `Brand mark similarity: ${Math.round(logoSim * 100)}% (risk: ${Math.round(logoRisk)}%)`,
        context: matchedRef
          ? `Compared against verified brand asset: ${matchedRef.replace('verified_brand_', '').replace('.png', '')}`
          : 'No registered brand mark matched.',
        active: isActive,
        suppressed: false,
        severity: isActive ? 'high' : logoRisk > 30 ? 'medium' : 'low',
        contribution: isActive ? 'Triggered severe signal — logo divergence ≥ 60%' : 'Logo within acceptable tolerance',
      });
    }
  }

  // ── Signal 3: Document / Image Manipulation ──
  if (manipulation) {
    const manipScore = manipulation.manipulation_score ?? 0;
    const riskLevel = manipulation.risk_level || 'LOW';
    const regions = (manipulation.suspicious_regions || []).length;

    signals.push({
      id: 'forensic_manipulation',
      label: 'Forensic ELA Integrity',
      detail: `Compression anomaly score: ${Math.round(manipScore)}% — ${riskLevel} risk`,
      context: regions > 0
        ? `${regions} localized gradient anomaly region(s) detected.`
        : 'Uniform compression coefficient — no localized splicing detected.',
      active: manipScore >= 60,
      suppressed: false,
      severity: manipScore >= 60 ? 'high' : manipScore > 20 ? 'medium' : 'low',
      contribution: manipScore >= 60 ? 'Tampered document — severe signal' : 'No significant manipulation detected',
    });
  }

  // ── Signal 4: Identity Coherence ──
  if (identity) {
    const coherence = identity.coherence_score ?? 1.0;
    const coherencePct = coherence <= 1 ? Math.round(coherence * 100) : Math.round(coherence);
    const lowCoherence = coherencePct < 50;

    signals.push({
      id: 'identity_coherence',
      label: 'Cross-Product Visual Identity',
      detail: `Catalog coherence: ${coherencePct}%`,
      context: lowCoherence
        ? 'Mixed visual styles suggest possible catalog stitching from multiple unrelated sources.'
        : 'Visual style is consistent across extracted product catalog.',
      active: false, // coherence alone never escalates
      suppressed: false,
      severity: lowCoherence ? 'medium' : 'low',
      contribution: 'Informational — does not independently drive escalation',
    });
  }

  // ── Corroboration Gate Status ──
  const severeSignals = signals.filter(s => s.active).length;
  const suppressedSignals = signals.filter(s => s.suppressed).length;

  // ── Tier Explanation ──
  const tierExplanation = (() => {
    if (isUnverifiable) return 'Domain unreachable. Scoring suspended — no evidence available.';
    if (tier === 'HIGH') return `${severeSignals} independently corroborated severe signals satisfied escalation threshold (≥ 2 required).`;
    if (tier === 'MEDIUM') return `${severeSignals} severe signal detected. Enhanced verification triggered. A 2nd corroborated signal is required for HIGH escalation.`;
    if (tier === 'LOW' && severeSignals === 0 && suppressedSignals > 0) return 'Strong visual matches found, but all originate from supplier/catalog sources — excluded from escalation by safety policy.';
    if (tier === 'LOW' && score > 20) return 'Visual signals detected but insufficient corroboration for escalation. Single uncorroborated matches are intentionally bounded at LOW to protect legitimate resellers.';
    return 'No suspicious visual evidence detected. Merchant approved for standard onboarding.';
  })();

  const analystActions = (() => {
    const actions = [];
    const hasLogoSevere = signals.find(s => s.id === 'logo_divergence' && s.active);
    const hasReuseSevere = signals.find(s => s.id === 'image_reuse' && s.active);
    const hasManipSevere = signals.find(s => s.id === 'forensic_manipulation' && s.active);
    const hasSupplierReuse = signals.find(s => s.id === 'image_reuse' && s.suppressed);

    if (hasManipSevere) {
      actions.push('Request original unedited document for independent verification.');
      actions.push('Perform physical certificate authentication with issuing authority.');
    }
    if (hasLogoSevere) {
      actions.push('Verify brand ownership with official trademark registry.');
      actions.push('Request brand authorization letter from claimed parent brand.');
    }
    if (hasReuseSevere) {
      actions.push('Escalate to senior risk operations for manual visual audit.');
      actions.push('Request original product photography from merchant.');
    }
    if (hasSupplierReuse && !hasReuseSevere) {
      actions.push('Request supplier/distributor authorization agreement.');
      actions.push('Verify merchant is an authorized reseller for matched brands.');
    }
    if (actions.length === 0) {
      if (tier === 'MEDIUM') {
        actions.push('Request additional business verification documentation.');
        actions.push('Confirm merchant contact details and business registration.');
      } else {
        actions.push('Proceed with standard merchant onboarding workflow.');
      }
    }
    return actions;
  })();

  return (
    <div className="card" style={{ marginBottom: '1.5rem', padding: '1.5rem' }}>
      {/* Header */}
      <div
        style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer', marginBottom: expanded ? '1.25rem' : 0 }}
        onClick={() => setExpanded(v => !v)}
        role="button"
        aria-expanded={expanded}
        tabIndex={0}
        onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') setExpanded(v => !v); }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
          <Info size={16} color="var(--amber)" />
          <span className="eyebrow">WHY THIS DECISION?</span>
        </div>
        {expanded ? <ChevronUp size={16} color="var(--muted)" /> : <ChevronDown size={16} color="var(--muted)" />}
      </div>

      {expanded && (
        <>
          {/* Tier Summary */}
          <div style={{ background: 'rgba(217,161,92,0.06)', border: '1px solid rgba(217,161,92,0.15)', borderRadius: '8px', padding: '0.85rem 1rem', marginBottom: '1.25rem' }}>
            <div style={{ fontSize: '13px', color: 'var(--cream)', lineHeight: 1.5 }}>
              {tierExplanation}
            </div>
          </div>

          {/* Signal Checklist */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginBottom: '1.25rem' }}>
            {signals.map((sig) => (
              <div key={sig.id} style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-start' }}>
                {/* Signal Icon */}
                <div style={{ flexShrink: 0, marginTop: '2px' }}>
                  {sig.active ? (
                    <AlertTriangle size={15} color="var(--risk-amber)" />
                  ) : sig.suppressed ? (
                    <CheckCircle2 size={15} color="var(--risk-green)" />
                  ) : (
                    <Circle size={15} color="var(--muted)" />
                  )}
                </div>

                {/* Signal Content */}
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', flexWrap: 'wrap', gap: '0.5rem' }}>
                    <span style={{ fontSize: '13px', fontWeight: 600, color: sig.active ? 'var(--cream)' : 'var(--muted)' }}>
                      {sig.label}
                    </span>
                    <span className="tag" style={{
                      background: sig.active ? 'rgba(230,100,74,0.18)' : sig.suppressed ? 'rgba(103,194,124,0.15)' : 'rgba(237,227,208,0.06)',
                      color: sig.active ? 'var(--risk-red)' : sig.suppressed ? 'var(--risk-green)' : 'var(--muted)',
                      border: `1px solid ${sig.active ? 'rgba(230,100,74,0.3)' : sig.suppressed ? 'rgba(103,194,124,0.25)' : 'var(--border)'}`,
                    }}>
                      {sig.active ? '⚑ SEVERE SIGNAL' : sig.suppressed ? '○ EXCLUDED' : '○ INFORMATIONAL'}
                    </span>
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--amber)', fontFamily: 'JetBrains Mono, monospace', marginTop: '0.2rem' }}>
                    {sig.detail}
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--muted)', marginTop: '0.15rem', lineHeight: 1.4 }}>
                    {sig.context}
                  </div>
                  <div style={{ fontSize: '11px', color: sig.active ? 'rgba(230,100,74,0.85)' : 'var(--muted)', marginTop: '0.15rem', fontStyle: 'italic' }}>
                    → {sig.contribution}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Corroboration Gate Summary */}
          <div style={{ borderTop: '1px solid var(--border)', paddingTop: '1rem', marginBottom: '1rem' }}>
            <span className="eyebrow" style={{ fontSize: '10px' }}>CORROBORATION GATE</span>
            <div style={{ marginTop: '0.5rem', fontSize: '12px', color: 'var(--muted)', lineHeight: 1.5 }}>
              <span style={{ color: severeSignals >= 2 ? 'var(--risk-red)' : severeSignals === 1 ? 'var(--amber)' : 'var(--risk-green)' }}>
                {severeSignals} severe signal{severeSignals !== 1 ? 's' : ''}
              </span>
              {' '}detected &nbsp;·&nbsp; {suppressedSignals} excluded (supplier safety)
              &nbsp;·&nbsp; Threshold for HIGH: ≥ 2 independent severe signals
            </div>
          </div>

          {/* Recommended Analyst Actions */}
          {analystActions.length > 0 && (
            <div style={{ background: 'rgba(217,161,92,0.04)', border: '1px solid var(--border)', borderRadius: '8px', padding: '0.85rem 1rem' }}>
              <span className="eyebrow" style={{ fontSize: '10px', marginBottom: '0.5rem', display: 'block' }}>RECOMMENDED ANALYST ACTIONS</span>
              {analystActions.map((action, i) => (
                <div key={i} style={{ fontSize: '12px', color: 'var(--cream)', marginTop: '0.3rem', display: 'flex', gap: '0.5rem', alignItems: 'flex-start' }}>
                  <span style={{ color: 'var(--amber)', flexShrink: 0 }}>→</span>
                  <span>{action}</span>
                </div>
              ))}
              <div style={{ marginTop: '0.75rem', fontSize: '10px', color: 'var(--muted)', fontStyle: 'italic' }}>
                These are analyst recommendations. This system never automatically rejects a merchant.
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
