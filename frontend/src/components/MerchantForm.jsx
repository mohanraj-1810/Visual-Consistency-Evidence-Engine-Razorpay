import React, { useState, useRef } from 'react';
import { Globe, Play, CheckCircle2, Loader2, Sparkles, X, Link2, ExternalLink, ShieldAlert } from 'lucide-react';

const ANALYSIS_STEPS = [
  { id: 'crawl', label: 'Website crawled' },
  { id: 'extract', label: 'Images extracted' },
  { id: 'prioritize', label: 'Important images identified' },
  { id: 'search', label: 'Online evidence searched' },
  { id: 'candidates', label: 'Candidate images collected' },
  { id: 'vit', label: 'ViT verification completed' },
  { id: 'logo', label: 'Logo checked' },
  { id: 'reuse', label: 'Image reuse checked' },
  { id: 'manipulation', label: 'Digital tampering checked' },
  { id: 'identity', label: 'Cross-image coherence checked' },
  { id: 'fusion', label: 'Multimodal risk fusion completed' },
];

const SAMPLE_URLS = [
  { name: '🟢 Standard Storefront (Clean)', url: 'https://example.com', description: 'Baseline standard web entity' },
  { name: '🟣 Anti-Bot Protected (WAF 403)', url: 'https://www.etsy.com', description: 'Anti-bot Cloudflare/WAF protected site' },
  { name: '🟡 Redirect Loop (Safety Limit)', url: 'https://httpbin.org/redirect/5', description: 'Exceeds 3-hop safety redirect limit' },
  { name: '🔵 Fintech Platform (Razorpay)', url: 'https://razorpay.com', description: 'Fintech & payment infrastructure brand platform' },
  { name: '⚪ Dead Domain (Unverifiable)', url: 'https://nonexistent-store-fake-12345.com', description: 'DNS failure / unreachable host' },
];

export default function MerchantForm({ onAnalyze, loading, currentSteps = {} }) {
  const [url, setUrl] = useState('https://example.com');
  const inputRef = useRef(null);

  const normalizeUrl = (raw) => {
    let trimmed = raw.trim();
    if (!trimmed) return '';
    if (!trimmed.startsWith('http://') && !trimmed.startsWith('https://')) {
      trimmed = 'https://' + trimmed;
    }
    return trimmed;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const finalUrl = normalizeUrl(url);
    if (!finalUrl) return;
    onAnalyze(finalUrl);
  };

  const handleSelectSample = (sampleUrl) => {
    setUrl(sampleUrl);
    if (inputRef.current) {
      inputRef.current.focus();
    }
  };

  const handleClear = () => {
    setUrl('');
    if (inputRef.current) {
      inputRef.current.focus();
    }
  };

  // Compute progress percentage
  const completedCount = ANALYSIS_STEPS.filter(
    (s) => currentSteps[s.id] === 'completed' || currentSteps[s.id] === 'done' || currentSteps.all_done
  ).length;
  const progressPct = currentSteps.all_done ? 100 : Math.round((completedCount / ANALYSIS_STEPS.length) * 100);

  return (
    <div className="card" style={{ marginBottom: '2rem', padding: '1.75rem' }}>
      <div className="card-title" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.65rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div
            style={{
              background: 'rgba(59, 130, 246, 0.15)',
              border: '1px solid rgba(59, 130, 246, 0.3)',
              padding: '0.5rem',
              borderRadius: '10px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Globe size={22} color="#60a5fa" />
          </div>
          <div>
            <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#ffffff', letterSpacing: '-0.01em' }}>
              Merchant Visual Risk Underwriting
            </div>
            <div style={{ fontSize: '0.82rem', color: '#94a3b8', fontWeight: 400 }}>
              Automated crawling, online candidate discovery, and ViT cosine verification
            </div>
          </div>
        </div>

        <span className="status-pill blue">
          <Sparkles size={13} />
          <span>AUTONOMOUS RISK AUDIT</span>
        </span>
      </div>

      <p style={{ color: '#cbd5e1', fontSize: '0.88rem', lineHeight: '1.5', marginTop: '0.5rem', marginBottom: '1.5rem' }}>
        Enter any merchant's website URL below. The engine crawls the domain, discovers online candidate visual evidence, verifies image similarity using Vision Transformers, and fuses all visual and text risk dimensions into an explainable decision-support dossier.
      </p>

      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: '1.25rem' }}>
          <label style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.6rem' }}>
            <span style={{ fontWeight: 700, color: '#f1f5f9', fontSize: '0.9rem' }}>Merchant Website URL</span>
            <span style={{ fontSize: '0.76rem', color: '#64748b' }}>Enter domain or storefront URL (e.g. store.com or https://example.com)</span>
          </label>

          {/* Upgraded Large Interactive Input Container */}
          <div
            style={{
              display: 'flex',
              gap: '0.75rem',
              alignItems: 'stretch',
              background: '#0d0e14',
              border: '1px solid #23242e',
              borderRadius: '12px',
              padding: '0.4rem',
              transition: 'all 0.2s ease',
              boxShadow: '0 4px 16px rgba(0, 0, 0, 0.4)',
            }}
            onFocus={(e) => {
              e.currentTarget.style.borderColor = '#3b82f6';
              e.currentTarget.style.boxShadow = '0 0 0 3px rgba(59, 130, 246, 0.25), 0 6px 24px rgba(0, 0, 0, 0.5)';
            }}
            onBlur={(e) => {
              if (!e.currentTarget.contains(e.relatedTarget)) {
                e.currentTarget.style.borderColor = '#23242e';
                e.currentTarget.style.boxShadow = '0 4px 16px rgba(0, 0, 0, 0.4)';
              }
            }}
          >
            {/* Left Icon */}
            <div style={{ display: 'flex', alignItems: 'center', paddingLeft: '0.85rem', color: '#3b82f6' }}>
              <Link2 size={20} />
            </div>

            {/* Input field */}
            <input
              ref={inputRef}
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="e.g. https://your-merchant-storefront.com"
              required
              autoComplete="off"
              spellCheck="false"
              style={{
                flex: 1,
                background: 'transparent',
                border: 'none',
                outline: 'none',
                color: '#ffffff',
                fontSize: '1.05rem',
                fontWeight: 500,
                padding: '0.7rem 0.5rem',
                fontFamily: 'inherit',
              }}
            />

            {/* Clear Button */}
            {url && (
              <button
                type="button"
                onClick={handleClear}
                title="Clear input"
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: '#64748b',
                  cursor: 'pointer',
                  padding: '0 0.6rem',
                  display: 'flex',
                  alignItems: 'center',
                  borderRadius: '6px',
                  transition: 'color 0.15s ease',
                }}
                onMouseEnter={(e) => (e.currentTarget.style.color = '#f8fafc')}
                onMouseLeave={(e) => (e.currentTarget.style.color = '#64748b')}
              >
                <X size={17} />
              </button>
            )}

            {/* Primary Action Button */}
            <button
              type="submit"
              disabled={loading || !url.trim()}
              className="btn-primary"
              style={{ minWidth: '220px', justifyContent: 'center' }}
            >
              {loading ? (
                <>
                  <Loader2 size={18} className="spinner" style={{ animation: 'spin 1s linear infinite' }} />
                  <span>ANALYZING RISK...</span>
                </>
              ) : (
                <>
                  <Play size={16} fill="currentColor" />
                  <span>ANALYZE MERCHANT</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Quick Sample Selector Pills with Archetype Badges */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', flexWrap: 'wrap', marginTop: '1rem' }}>
          <span style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 600 }}>Test Archetypes:</span>
          {SAMPLE_URLS.map((sample, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handleSelectSample(sample.url)}
              className="preset-chip"
              title={sample.description}
              style={{
                borderColor: url === sample.url ? '#3b82f6' : undefined,
                background: url === sample.url ? 'rgba(59, 130, 246, 0.15)' : undefined,
                color: url === sample.url ? '#93c5fd' : undefined,
              }}
            >
              <ExternalLink size={12} />
              <span>{sample.name}</span>
            </button>
          ))}
        </div>
      </form>

      {/* Real-time Progress Stepper when Loading */}
      {loading && (
        <div
          style={{
            marginTop: '1.75rem',
            padding: '1.25rem 1.5rem',
            background: 'rgba(14, 15, 20, 0.95)',
            border: '1px solid #23242e',
            borderRadius: '12px',
            backdropFilter: 'blur(16px)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span className="pulse-dot blue"></span>
              <strong style={{ fontSize: '0.9rem', color: '#60a5fa' }}>Autonomous Analysis Pipeline Streaming ({progressPct}%)</strong>
            </div>
            <span className="data-chip highlight">ViT Engine & Serper Discovery</span>
          </div>

          {/* Smooth Gradient Progress Bar */}
          <div style={{ background: '#1c1e28', height: '6px', borderRadius: '3px', overflow: 'hidden', marginBottom: '1.25rem' }}>
            <div
              style={{
                width: `${Math.max(5, progressPct)}%`,
                height: '100%',
                background: 'linear-gradient(90deg, #3b82f6 0%, #8b5cf6 50%, #10b981 100%)',
                transition: 'width 0.4s ease',
              }}
            />
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
              gap: '0.5rem',
            }}
          >
            {ANALYSIS_STEPS.map((step) => {
              const isDone = currentSteps[step.id] === 'completed' || currentSteps[step.id] === 'done' || currentSteps.all_done;
              const isActive = currentSteps[step.id] === 'running' || currentSteps[step.id] === 'in_progress';

              return (
                <div
                  key={step.id}
                  className={`step-item ${isDone ? 'done' : isActive ? 'active' : ''}`}
                >
                  {isDone ? (
                    <CheckCircle2 size={16} color="#10b981" />
                  ) : isActive ? (
                    <Loader2 size={16} color="#3b82f6" style={{ animation: 'spin 1s linear infinite' }} />
                  ) : (
                    <div
                      style={{
                        width: '14px',
                        height: '14px',
                        borderRadius: '50%',
                        border: '1.5px solid #334155',
                      }}
                    />
                  )}
                  <span>{step.label}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
