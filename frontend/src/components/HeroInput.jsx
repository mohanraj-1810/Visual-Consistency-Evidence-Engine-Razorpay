import React, { useState, useRef } from 'react';
import { Link2, Play, Loader2, X, CheckCircle2, ArrowRight } from 'lucide-react';

const SAMPLE_PRESETS = [
  { name: 'Standard Storefront', url: 'https://example.com', desc: 'Baseline clean entity' },
  { name: 'Anti-Bot (403)', url: 'https://www.etsy.com', desc: 'Cloudflare / WAF protected' },
  { name: 'Redirect Loop', url: 'https://httpbin.org/redirect/5', desc: 'Exceeds 3-hop safety limit' },
  { name: 'Fintech Platform', url: 'https://razorpay.com', desc: 'Infrastructure brand platform' },
  { name: 'Dead Domain', url: 'https://nonexistent-store-fake-12345.com', desc: 'Unreachable host' },
];

export default function HeroInput({
  onAnalyze,
  loading,
  currentSteps = {},
  pipelineStages = [],
  getStageStatus,
  feedItems = [],
}) {
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
    if (inputRef.current) inputRef.current.focus();
  };

  const handleClear = () => {
    setUrl('');
    if (inputRef.current) inputRef.current.focus();
  };

  return (
    <div style={{ width: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1.25rem', marginTop: '0.75rem' }}>
      {/* ── URL Input Card ── */}
      <form onSubmit={handleSubmit} style={{ width: '100%', maxWidth: '680px' }}>
        <div className="url-input-card">
          <div className="url-input-icon">
            <Link2 size={18} />
          </div>

          <input
            ref={inputRef}
            type="text"
            className="url-input-field"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="Enter merchant storefront URL (e.g. store.com)..."
            required
            autoComplete="off"
            spellCheck="false"
            disabled={loading}
          />

          {url && !loading && (
            <button
              type="button"
              className="url-input-clear"
              onClick={handleClear}
              title="Clear input"
              aria-label="Clear URL"
            >
              <X size={16} />
            </button>
          )}

          <div className="url-input-submit">
            <button
              type="submit"
              disabled={loading || !url.trim()}
              className="btn-primary"
            >
              {loading ? (
                <>
                  <Loader2 size={15} className="spinner" />
                  <span>ANALYZING...</span>
                </>
              ) : (
                <>
                  <Play size={13} fill="currentColor" />
                  <span>INITIATE ANALYSIS</span>
                </>
              )}
            </button>
          </div>
        </div>
      </form>

      {/* ── Quick Test Preset Pills ── */}
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem' }}>
        <span className="eyebrow" style={{ fontSize: '10px' }}>QUICK TEST ARCHETYPES</span>
        <div className="preset-chips">
          {SAMPLE_PRESETS.map((preset, idx) => (
            <button
              key={idx}
              type="button"
              className={`preset-chip ${url === preset.url ? 'active' : ''}`}
              onClick={() => handleSelectSample(preset.url)}
              title={preset.desc}
              disabled={loading}
            >
              <span>{preset.name}</span>
            </button>
          ))}
        </div>
      </div>

      {/* ── Loading State: Pipeline Stepper & Live Evidence Feed ── */}
      {loading && (
        <div style={{ width: '100%', maxWidth: '680px', display: 'flex', flexDirection: 'column', gap: '1.25rem', marginTop: '1rem' }}>
          {/* Stepper */}
          <div className="pipeline-stepper" role="progressbar" aria-label="Pipeline progress">
            {pipelineStages.map((stage, idx) => {
              const status = getStageStatus ? getStageStatus(stage) : 'idle';
              return (
                <div key={stage.id} className="pipeline-stage">
                  <div className={`pipeline-connector ${status === 'done' ? 'done' : ''}`} />
                  <div className={`pipeline-dot ${status}`}>
                    {status === 'done' ? (
                      <CheckCircle2 size={14} />
                    ) : status === 'active' ? (
                      <Loader2 size={13} className="spinner" color="var(--amber)" />
                    ) : (
                      <span style={{ width: '5px', height: '5px', borderRadius: '50%', background: 'var(--muted)' }} />
                    )}
                  </div>
                  <span className={`pipeline-label ${status}`}>
                    {stage.label}
                  </span>
                </div>
              );
            })}
          </div>

          {/* Live Evidence Stream Feed */}
          {feedItems.length > 0 && (
            <div className="live-feed" aria-live="polite">
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid var(--border)', paddingBottom: '0.4rem', marginBottom: '0.25rem' }}>
                <span className="eyebrow" style={{ fontSize: '10px' }}>LIVE EVIDENCE STREAM</span>
                <span className="font-mono" style={{ fontSize: '10px', color: 'var(--amber)' }}>STREAMING SSE/WS</span>
              </div>
              {feedItems.slice(-5).map((item, i) => {
                const date = new Date(item.ts);
                const timeStr = `${String(date.getMinutes()).padStart(2, '0')}:${String(date.getSeconds()).padStart(2, '0')}`;
                return (
                  <div key={i} className="feed-item visible">
                    <span className="feed-time">{timeStr}</span>
                    <span className="feed-bullet">+</span>
                    <span className="feed-text">{item.msg}</span>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
