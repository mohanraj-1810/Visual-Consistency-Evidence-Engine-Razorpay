import React, { useState, useCallback, useRef } from 'react';

import Header           from './components/Header';
import HeroInput        from './components/HeroInput';
import DemoMode         from './components/DemoMode';
import RiskCards        from './components/RiskCards';
import WhyDecision      from './components/WhyDecision';
import MerchantFingerprint from './components/MerchantFingerprint';
import ClaimVsEvidence  from './components/ClaimVsEvidence';
import EvidenceFusionCards from './components/EvidenceFusionCards';
import EvidenceGrid     from './components/EvidenceGrid';
import PipelinePerformance from './components/PipelinePerformance';
import HeatmapViewer    from './components/HeatmapViewer';
import AnalysisCounter  from './components/AnalysisCounter';
import ErrorBoundary    from './components/ErrorBoundary';

import { streamWebsiteAnalysis } from './api/client';
import { AlertTriangle } from 'lucide-react';

// ── Pipeline stage definitions (drives HeroInput stepper) ───────────────────
const PIPELINE_STAGES = [
  { id: 'crawl',     label: 'Crawl'     },
  { id: 'extract',   label: 'Extract'   },
  { id: 'search',    label: 'Search'    },
  { id: 'forensics', label: 'Forensics' },
  { id: 'fusion',    label: 'Fusion'    },
];

// Map fine-grained backend step IDs onto the 5 display stages
const STEP_TO_STAGE = {
  crawl:        'crawl',
  extract:      'extract',
  prioritize:   'extract',
  search:       'search',
  candidates:   'search',
  vit:          'search',
  logo:         'forensics',
  reuse:        'forensics',
  manipulation: 'forensics',
  identity:     'forensics',
  fusion:       'fusion',
  completed:    'fusion',
};

export default function App() {
  const [result,       setResult]       = useState(null);
  const [loading,      setLoading]      = useState(false);
  const [error,        setError]        = useState(null);
  // currentSteps: { [stepId]: 'in_progress' | 'completed' | 'done' }
  const [currentSteps, setCurrentSteps] = useState({});
  // feedItems: array of { ts, msg } for the live evidence stream
  const [feedItems,    setFeedItems]    = useState([]);

  // Timing state for AnalysisCounter
  const [startTs, setStartTs] = useState(null);
  const [endTs,   setEndTs]   = useState(null);

  // Keep a ref to the stream cleanup fn so we can cancel mid-flight
  const cleanupRef = useRef(null);

  // ── getStageStatus: maps a stage object → 'done' | 'active' | 'idle' ─────
  const getStageStatus = useCallback((stage) => {
    // A stage is done when any of its child steps are completed/done,
    // or when a later stage has started.
    const stageIndex = PIPELINE_STAGES.findIndex(s => s.id === stage.id);

    // Find the highest stage that has any activity
    let highestActiveIndex = -1;
    for (const [stepId, status] of Object.entries(currentSteps)) {
      const mappedStage = STEP_TO_STAGE[stepId] || stepId;
      const idx = PIPELINE_STAGES.findIndex(s => s.id === mappedStage);
      if (idx > highestActiveIndex && (status === 'in_progress' || status === 'completed' || status === 'done')) {
        highestActiveIndex = idx;
      }
    }

    if (currentSteps.all_done) return stageIndex <= highestActiveIndex ? 'done' : 'idle';
    if (stageIndex < highestActiveIndex) return 'done';
    if (stageIndex === highestActiveIndex) {
      // Active: at least one step in this stage is in_progress
      const hasActive = Object.entries(currentSteps).some(([stepId, status]) => {
        return STEP_TO_STAGE[stepId] === stage.id && status === 'in_progress';
      });
      return hasActive ? 'active' : 'done';
    }
    return 'idle';
  }, [currentSteps]);

  // ── handleAnalyze: called by HeroInput on form submit ─────────────────────
  const handleAnalyze = useCallback((url) => {
    // Cancel any in-flight stream
    if (cleanupRef.current) cleanupRef.current();

    setLoading(true);
    setError(null);
    setResult(null);
    setCurrentSteps({});
    setFeedItems([]);
    setStartTs(Date.now());
    setEndTs(null);

    const cleanup = streamWebsiteAnalysis(
      url,
      // onStep
      (stepEvent) => {
        const stepId = stepEvent.step;
        setCurrentSteps(prev => ({
          ...prev,
          [stepId]: stepEvent.status || 'completed',
        }));
        if (stepEvent.message) {
          setFeedItems(prev => [...prev, { ts: Date.now(), msg: stepEvent.message }]);
        }
      },
      // onResult
      (analysisData) => {
        const now = Date.now();
        setCurrentSteps(prev => ({ ...prev, all_done: true }));
        setResult(analysisData);
        setLoading(false);
        setEndTs(now);
        cleanupRef.current = null;
      },
      // onError
      (err) => {
        console.error('Analysis error:', err);
        setError(err.message || 'Analysis failed. Make sure the backend is running.');
        setLoading(false);
        setEndTs(Date.now());
        cleanupRef.current = null;
      }
    );

    cleanupRef.current = cleanup;
    return cleanup;
  }, []);

  // ── handleDemoResult: called by DemoMode when a fixture result is ready ───
  const handleDemoResult = useCallback((demoData) => {
    setResult(demoData);
    setError(null);
    setLoading(false);
    setCurrentSteps({ all_done: true });
    setFeedItems([]);
    setStartTs(null);
    setEndTs(null);
  }, []);

  // ── handleReset: clears result and error ──────────────────────────────────
  const handleReset = useCallback(() => {
    setResult(null);
    setError(null);
    setCurrentSteps({});
    setFeedItems([]);
  }, []);

  // BUG-04 FIX: candidate_evidence is the list to show in EvidenceFusionCards
  // (those are the online web + platform ViT candidates).
  // result.evidence is the fused asset evidence list used in EvidenceGrid internally.
  const candidateEvidence = result?.candidate_evidence ?? [];

  return (
    <>
      {/* Skip-to-content for accessibility */}
      <a href="#main-content" className="skip-to-content">Skip to content</a>

      {/* Fixed-position analysis timer (BUG-05 FIX: now mounts with proper state) */}
      <AnalysisCounter
        startTs={startTs}
        endTs={endTs}
        loading={loading}
        visible={startTs !== null}
      />

      <Header />

      <main id="main-content" className="page-container">

        {/* ── Hero Section: Cinematic headline + URL input ─────────────────── */}
        <section className="hero-section">
          {/* Background image layer — dims once analysis starts */}
          <div
            className="hero-bg"
            data-stage={result ? '3' : loading ? '1' : '0'}
            aria-hidden="true"
          />

          <div className="hero-content">
            <span className="eyebrow">RAZORPAY · VISUAL RISK INTELLIGENCE</span>

            <div className="hero-headline-wrap">
              <h1 className="hero-headline active">
                {loading
                  ? 'Analysing\nMerchant Evidence…'
                  : result
                  ? 'Risk Dossier\nReady'
                  : 'Is this merchant\nwho they claim to be?'}
              </h1>
            </div>

            <p style={{
              fontFamily: 'Inter, sans-serif',
              fontSize: '15px',
              color: 'var(--muted)',
              maxWidth: '560px',
              lineHeight: 1.6,
              textAlign: 'center',
            }}>
              Multimodal visual intelligence engine — crawls the merchant website,
              discovers online candidate evidence, verifies with Vision Transformers,
              and produces an explainable underwriting dossier.
            </p>

            {/* BUG-06 & BUG-07 FIX: use HeroInput with pipelineStages + getStageStatus */}
            <HeroInput
              onAnalyze={handleAnalyze}
              loading={loading}
              currentSteps={currentSteps}
              pipelineStages={PIPELINE_STAGES}
              getStageStatus={getStageStatus}
              feedItems={feedItems}
            />
          </div>
        </section>

        {/* ── Demo Scenarios ───────────────────────────────────────────────── */}
        {/* BUG-08 FIX: DemoMode is now rendered */}
        {!loading && (
          <section className="section-block" aria-label="Demo scenarios">
            <div className="section-header">
              <span className="eyebrow">DETERMINISTIC DEMOS</span>
              <h2 className="section-headline">Judge Walkthrough Scenarios</h2>
              <p className="section-subtext">
                Pre-built fixture cases that run offline — no live crawl dependency.
                Each demonstrates a distinct risk tier and evidence interpretation pathway.
              </p>
            </div>
            <DemoMode onResult={handleDemoResult} loading={loading} />
          </section>
        )}

        {/* ── Error Banner ─────────────────────────────────────────────────── */}
        {error && (
          <div
            className="notice-banner amber-notice"
            style={{ marginTop: '2rem' }}
            role="alert"
          >
            <AlertTriangle size={18} color="var(--risk-amber)" style={{ flexShrink: 0, marginTop: '2px' }} />
            <div>
              <div className="notice-banner-title">Analysis Notice</div>
              <div className="notice-banner-body">{error}</div>
            </div>
          </div>
        )}

        {/* ── Results ──────────────────────────────────────────────────────── */}
        {result && (
          <ErrorBoundary onReset={handleReset}>

            {/* Section 1: Verdict + Score Cards */}
            <section className="section-block" aria-label="Risk verdict">
              <RiskCards
                fusion={result.fusion}
                claims={result.claims}
                webDetectionMode={result.web_detection_mode}
                webDetectionSimulated={result.web_detection_simulated}
              />
            </section>

            {/* Section 2: Why This Decision (BUG-08 FIX) */}
            <section className="section-block" aria-label="Decision explanation">
              <WhyDecision
                fusion={result.fusion}
                reuse={result.reuse}
                logo={result.logo}
                manipulation={result.manipulation}
                identity={result.identity}
              />
            </section>

            {/* Section 3: Visual Merchant Profile (BUG-08 FIX) */}
            <section className="section-block" aria-label="Merchant fingerprint">
              <MerchantFingerprint
                fusion={result.fusion}
                reuse={result.reuse}
                logo={result.logo}
                manipulation={result.manipulation}
                identity={result.identity}
              />
            </section>

            {/* Section 4: Pipeline Performance (BUG-08 FIX) */}
            <section aria-label="Pipeline performance">
              <PipelinePerformance fusion={result.fusion} result={result} />
            </section>

            {/* Section 5: Claims vs Evidence */}
            <section className="section-block" aria-label="Claims vs evidence">
              <div className="section-header">
                <span className="eyebrow">EVIDENCE AUDIT</span>
                <h2 className="section-headline">Claims vs. Visual Evidence</h2>
                <p className="section-subtext">
                  Each merchant claim is cross-referenced against the multimodal evidence gathered.
                </p>
              </div>
              <ClaimVsEvidence
                claimsReasoning={result.claims_reasoning}
                structuredEvidence={result.structured_evidence}
                claims={result.claims}
              />
            </section>

            {/* Section 6: Candidate Evidence Fusion Cards (BUG-04 FIX) */}
            {candidateEvidence.length > 0 && (
              <section className="section-block" aria-label="Candidate evidence">
                <div className="section-header">
                  <span className="eyebrow">ONLINE CANDIDATE DISCOVERY</span>
                  <h2 className="section-headline">Evidence Fusion Exhibits</h2>
                  <p className="section-subtext">
                    Visual assets discovered via web reverse search and verified via ViT cosine embeddings.
                  </p>
                </div>
                <EvidenceFusionCards evidence={candidateEvidence} />
              </section>
            )}

            {/* Section 7: 4-Metric Evidence Grid */}
            <section className="section-block" aria-label="Evidence metrics">
              <div className="section-header">
                <span className="eyebrow">FORENSIC METRICS</span>
                <h2 className="section-headline">Visual Risk Breakdown</h2>
              </div>
              <EvidenceGrid
                reuse={result.reuse}
                logo={result.logo}
                manipulation={result.manipulation}
                identity={result.identity}
              />
            </section>

            {/* Section 8: Deep-dive tabs — heatmap, forensics, JSON */}
            <section className="section-block" aria-label="Deep analysis">
              <div className="section-header">
                <span className="eyebrow">DEEP ANALYSIS</span>
                <h2 className="section-headline">Visual Forensics & Dossier</h2>
              </div>
              <HeatmapViewer result={result} />
            </section>

          </ErrorBoundary>
        )}

      </main>

      {/* ── Footer ───────────────────────────────────────────────────────── */}
      <footer className="site-footer" role="contentinfo">
        <span className="footer-wordmark">Visual Risk Intelligence Engine</span>
        <p className="footer-copy">
          🛡️ Razorpay AI Risk Manager · Decision Support System for Human Risk Analysts
          <br />
          Never automatically rejects merchants — all outputs are advisory.
        </p>
      </footer>
    </>
  );
}
