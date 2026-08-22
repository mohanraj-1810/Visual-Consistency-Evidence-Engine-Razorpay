import React, { useState, useRef } from 'react';
import { Globe, Play, CheckCircle2, Loader2, Sparkles, X, Link2, ExternalLink } from 'lucide-react';

const ANALYSIS_STEPS = [
  { id: 'crawl', label: 'Website crawled' },
  { id: 'extract', label: 'Images extracted' },
  { id: 'prioritize', label: 'Important images identified' },
  { id: 'search', label: 'Online evidence searched' },
  { id: 'candidates', label: 'Candidate images collected' },
  { id: 'vit', label: 'ViT verification completed' },
  { id: 'logo', label: 'Logo checked' },
  { id: 'reuse', label: 'Image reuse checked' },
  { id: 'manipulation', label: 'Manipulation checked' },
  { id: 'identity', label: 'Identity checked' },
  { id: 'fusion', label: 'Risk fusion completed' },
];

const SAMPLE_URLS = [
  { name: 'Artisan Pottery (Clean)', url: 'https://example.com' },
  { name: 'Live Web Test', url: 'https://httpbin.org' },
  { name: 'Stripe Brand Wikipedia', url: 'https://en.wikipedia.org/wiki/Stripe,_Inc.' },
  { name: 'Razorpay Brand Asset', url: 'https://razorpay.com' },
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

  return (
    <div className="card" style={{ marginBottom: '2rem', padding: '1.75rem' }}>
      <div className="card-title" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
          <div style={{ background: 'rgba(99, 102, 241, 0.15)', padding: '0.45rem', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Globe size={22} color="#818cf8" />
          </div>
          <div>
            <div style={{ fontSize: '1.2rem', fontWeight: 800, color: '#f8fafc', letterSpacing: '-0.01em' }}>
              Visual Merchant Risk Engine
            </div>
            <div style={{ fontSize: '0.8rem', color: '#94a3b8', fontWeight: 400 }}>
              Autonomous Visual Intelligence & Multimodal Risk Verification
            </div>
          </div>
        </div>
        <span style={{ fontSize: '0.78rem', color: '#a5b4fc', background: '#0f172a', padding: '0.35rem 0.85rem', borderRadius: '20px', border: '1px solid rgba(99, 102, 241, 0.3)', fontWeight: 600 }}>
          URL Ingestion Only • Auto Evidence Discovery
        </span>
      </div>

      <p style={{ color: '#cbd5e1', fontSize: '0.88rem', lineHeight: '1.5', marginTop: '0.5rem', marginBottom: '1.5rem' }}>
        Enter any merchant's website URL below. The engine crawls the domain, discovers online candidate visual evidence, verifies image similarity using Vision Transformers, and fuses all visual and text risk dimensions into an explainable decision-support dossier.
      </p>

      <form onSubmit={handleSubmit}>
        <div className="form-group" style={{ marginBottom: '1rem' }}>
          <label className="form-label" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span style={{ fontWeight: 700, color: '#f1f5f9', fontSize: '0.9rem' }}>Merchant Website URL</span>
            <span style={{ fontSize: '0.76rem', color: '#64748b' }}>Enter domain or full URL (e.g. example.com or https://store.com)</span>
          </label>

          {/* Upgraded Large Interactive Input Container */}
          <div
            style={{
              display: 'flex',
              gap: '0.75rem',
              alignItems: 'stretch',
              background: '#0a0f1d',
              border: '2px solid #334155',
              borderRadius: '12px',
              padding: '0.4rem',
              transition: 'all 0.2s ease',
              boxShadow: '0 4px 14px rgba(0, 0, 0, 0.3)',
            }}
            onFocus={(e) => {
              e.currentTarget.style.borderColor = '#6366f1';
              e.currentTarget.style.boxShadow = '0 0 0 3px rgba(99, 102, 241, 0.25), 0 4px 20px rgba(0, 0, 0, 0.4)';
            }}
            onBlur={(e) => {
              if (!e.currentTarget.contains(e.relatedTarget)) {
                e.currentTarget.style.borderColor = '#334155';
                e.currentTarget.style.boxShadow = '0 4px 14px rgba(0, 0, 0, 0.3)';
              }
            }}
          >
            {/* Left Icon */}
            <div style={{ display: 'flex', alignItems: 'center', paddingLeft: '0.75rem', color: '#6366f1' }}>
              <Link2 size={20} />
            </div>

            {/* Input field */}
            <input
              ref={inputRef}
              type="text"
              className="url-live-input"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="e.g. https://your-merchant-website.com or brand.com"
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
                padding: '0.65rem 0.5rem',
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
              style={{
                background: loading
                  ? 'linear-gradient(135deg, #4338ca 0%, #3730a3 100%)'
                  : 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)',
                color: '#ffffff',
                border: 'none',
                borderRadius: '8px',
                padding: '0.75rem 1.6rem',
                fontSize: '0.95rem',
                fontWeight: 700,
                letterSpacing: '0.03em',
                cursor: loading || !url.trim() ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '0.55rem',
                minWidth: '210px',
                transition: 'all 0.2s ease',
                boxShadow: '0 2px 8px rgba(79, 70, 229, 0.4)',
              }}
              onMouseEnter={(e) => {
                if (!loading && url.trim()) {
                  e.currentTarget.style.transform = 'translateY(-1px)';
                  e.currentTarget.style.boxShadow = '0 4px 14px rgba(99, 102, 241, 0.5)';
                }
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = '0 2px 8px rgba(79, 70, 229, 0.4)';
              }}
            >
              {loading ? (
                <>
                  <Loader2 size={18} className="spinner" />
                  <span>ANALYZING WEBSITE...</span>
                </>
              ) : (
                <>
                  <Play size={16} fill="currentColor" />
                  <span>ANALYZE WEBSITE</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Quick Sample Selector Pills */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', flexWrap: 'wrap', marginTop: '0.85rem' }}>
          <span style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 600 }}>Quick test targets:</span>
          {SAMPLE_URLS.map((sample, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handleSelectSample(sample.url)}
              style={{
                background: url === sample.url ? 'rgba(99, 102, 241, 0.2)' : '#0f172a',
                border: url === sample.url ? '1px solid #6366f1' : '1px solid #334155',
                color: url === sample.url ? '#c7d2fe' : '#94a3b8',
                borderRadius: '6px',
                padding: '0.35rem 0.75rem',
                fontSize: '0.78rem',
                fontWeight: 500,
                cursor: 'pointer',
                transition: 'all 0.15s ease',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.35rem',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = '#6366f1';
                e.currentTarget.style.color = '#ffffff';
              }}
              onMouseLeave={(e) => {
                if (url !== sample.url) {
                  e.currentTarget.style.borderColor = '#334155';
                  e.currentTarget.style.color = '#94a3b8';
                }
              }}
            >
              <span>{sample.name}</span>
              <span style={{ fontSize: '0.7rem', color: '#64748b' }}>({sample.url.replace('https://', '')})</span>
            </button>
          ))}
        </div>

        {/* Live Real-Time Stepper During Analysis */}
        {loading && (
          <div
            style={{
              marginTop: '1.5rem',
              background: '#0b1120',
              border: '1px solid #1e293b',
              borderRadius: '12px',
              padding: '1.25rem 1.5rem',
              boxShadow: '0 4px 16px rgba(0, 0, 0, 0.4)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#818cf8', fontWeight: 700, fontSize: '0.92rem' }}>
                <Sparkles size={16} />
                <span>Live Multimodal Risk Pipeline Execution</span>
              </div>
              <span style={{ fontSize: '0.75rem', color: '#64748b' }}>Real-time execution signals</span>
            </div>

            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                gap: '0.6rem',
              }}
            >
              {ANALYSIS_STEPS.map((step, idx) => {
                const isDone = currentSteps[step.id] === 'completed' || currentSteps['all_done'];
                const isRunning = !isDone && (idx === 0 || currentSteps[ANALYSIS_STEPS[idx - 1]?.id] === 'completed');

                return (
                  <div
                    key={step.id}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem',
                      padding: '0.5rem 0.75rem',
                      borderRadius: '6px',
                      background: isDone ? 'rgba(34, 197, 94, 0.08)' : isRunning ? 'rgba(99, 102, 241, 0.14)' : '#0f172a',
                      border: isDone ? '1px solid rgba(34, 197, 94, 0.3)' : isRunning ? '1px solid #6366f1' : '1px solid #1e293b',
                      color: isDone ? '#86efac' : isRunning ? '#c7d2fe' : '#64748b',
                      fontSize: '0.8rem',
                      fontWeight: isDone || isRunning ? 500 : 400,
                      transition: 'all 0.2s ease',
                    }}
                  >
                    {isDone ? (
                      <CheckCircle2 size={15} color="#22c55e" style={{ flexShrink: 0 }} />
                    ) : isRunning ? (
                      <Loader2 size={15} color="#818cf8" className="spinner" style={{ flexShrink: 0 }} />
                    ) : (
                      <div
                        style={{
                          width: '14px',
                          height: '14px',
                          borderRadius: '50%',
                          border: '1.5px solid #475569',
                          flexShrink: 0,
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
      </form>
    </div>
  );
}
