import React, { useState } from 'react';
import { Play, Loader2, CheckCircle2, ShieldCheck, AlertTriangle, Package } from 'lucide-react';

const API_BASE = (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_URL) || 'http://127.0.0.1:8000';

const SCENARIOS = [
  {
    id: 'clean',
    label: 'Clean Merchant',
    icon: ShieldCheck,
    iconColor: 'var(--risk-green)',
    tagClass: 'tag-green',
    tagLabel: 'LOW RISK',
    merchant: 'Terracotta Heritage Studio',
    category: 'Handcrafted Ceramics',
    description: 'Zero external image matches. Proprietary artisanal photography. Complete disclosures.',
    goal: 'Demonstrates 0% false positive rate on authentic merchants.',
  },
  {
    id: 'supplier',
    label: 'Supplier / Ambiguous',
    icon: Package,
    iconColor: 'var(--amber)',
    tagClass: 'tag-amber',
    tagLabel: 'LOW / ONBOARDING',
    merchant: 'Urban Velocity Footwear',
    category: 'Footwear Reseller',
    description: 'Authorized supplier catalog images. Strong visual overlap — but source is legitimate distributor.',
    goal: 'Demonstrates intelligent evidence interpretation: not all similarity is fraud.',
  },
  {
    id: 'counterfeit',
    label: 'Corroborated Risk',
    icon: AlertTriangle,
    iconColor: 'var(--risk-amber)',
    tagClass: 'tag-amber',
    tagLabel: 'MEDIUM / VERIFY',
    merchant: 'Luxe Atelier Outlet',
    category: 'Luxury Designer Handbags',
    description: 'Stolen handbag imagery (99.8% ViT similarity) + distorted trademark logo (62.9% divergence).',
    goal: 'Demonstrates multi-vector corroboration triggering enhanced verification.',
  },
];

export default function DemoMode({ onResult, loading: globalLoading }) {
  const [loadingId, setLoadingId] = useState(null);
  const [lastRunId, setLastRunId] = useState(null);
  const [error, setError] = useState(null);

  const runDemo = async (scenarioId) => {
    if (globalLoading || loadingId) return;
    setLoadingId(scenarioId);
    setError(null);

    try {
      const res = await fetch(`${API_BASE}/api/demo-scenario/${scenarioId}`, {
        signal: AbortSignal.timeout(60000),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Demo execution failed (${res.status})`);
      }
      const data = await res.json();
      setLastRunId(scenarioId);
      onResult(data);
    } catch (e) {
      setError(e.message || 'Demo scenario failed.');
    } finally {
      setLoadingId(null);
    }
  };

  return (
    <div style={{ marginBottom: '1rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem', flexWrap: 'wrap', gap: '0.5rem' }}>
        <span className="eyebrow">DEMO SCENARIOS — DETERMINISTIC JUDGE WALKTHROUGH</span>
        <span className="font-mono" style={{ fontSize: '10px', color: 'var(--muted)' }}>
          Offline fixture · No live search dependency
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '0.85rem' }}>
        {SCENARIOS.map((s) => {
          const Icon = s.icon;
          const isRunning = loadingId === s.id;
          const isDone = lastRunId === s.id && !loadingId;

          return (
            <div
              key={s.id}
              className="card"
              style={{
                padding: '1.1rem',
                cursor: globalLoading || loadingId ? 'not-allowed' : 'pointer',
                opacity: (globalLoading || (loadingId && loadingId !== s.id)) ? 0.5 : 1,
                border: isDone ? '1px solid rgba(103,194,124,0.35)' : '1px solid var(--border)',
                transition: 'all 0.2s ease',
              }}
              onClick={() => runDemo(s.id)}
              role="button"
              tabIndex={0}
              onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') runDemo(s.id); }}
              aria-label={`Run demo: ${s.label}`}
            >
              {/* Header */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.65rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Icon size={16} color={s.iconColor} />
                  <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--cream)' }}>{s.label}</span>
                </div>
                <span className={`tag ${s.tagClass}`} style={{ fontSize: '9px' }}>{s.tagLabel}</span>
              </div>

              {/* Merchant info */}
              <div style={{ fontSize: '11px', color: 'var(--amber)', fontFamily: 'JetBrains Mono, monospace', marginBottom: '0.25rem' }}>{s.merchant}</div>
              <div style={{ fontSize: '10px', color: 'var(--muted)', marginBottom: '0.5rem' }}>{s.category}</div>

              {/* Description */}
              <div style={{ fontSize: '11px', color: 'var(--muted)', lineHeight: 1.45, marginBottom: '0.65rem' }}>{s.description}</div>

              {/* Goal */}
              <div style={{ fontSize: '10px', color: 'var(--amber)', fontStyle: 'italic', lineHeight: 1.4, borderTop: '1px solid var(--border)', paddingTop: '0.5rem' }}>
                {s.goal}
              </div>

              {/* Run Button */}
              <button
                className="btn-primary"
                style={{ width: '100%', marginTop: '0.75rem', padding: '0.45rem', fontSize: '11px', justifyContent: 'center', opacity: (globalLoading || (loadingId && loadingId !== s.id)) ? 0.4 : 1 }}
                disabled={!!globalLoading || !!loadingId}
                onClick={e => { e.stopPropagation(); runDemo(s.id); }}
              >
                {isRunning ? (
                  <><Loader2 size={13} className="spinner" /><span>RUNNING...</span></>
                ) : isDone ? (
                  <><CheckCircle2 size={13} /><span>DONE — RUN AGAIN</span></>
                ) : (
                  <><Play size={11} fill="currentColor" /><span>RUN SCENARIO</span></>
                )}
              </button>
            </div>
          );
        })}
      </div>

      {error && (
        <div className="notice-banner red-notice" style={{ marginTop: '0.75rem' }}>
          <AlertTriangle size={15} color="var(--risk-red)" style={{ flexShrink: 0 }} />
          <div style={{ fontSize: '12px' }}>{error} — Make sure the backend is running.</div>
        </div>
      )}
    </div>
  );
}
