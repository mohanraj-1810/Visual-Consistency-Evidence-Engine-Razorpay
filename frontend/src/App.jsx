import React, { useState, useEffect, useRef, useCallback } from 'react';
import HeroInput from './components/HeroInput';
import RiskCards from './components/RiskCards';
import ClaimVsEvidence from './components/ClaimVsEvidence';
import EvidenceGrid from './components/EvidenceGrid';
import EvidenceFusionCards from './components/EvidenceFusionCards';
import HeatmapViewer from './components/HeatmapViewer';
import ErrorBoundary from './components/ErrorBoundary';
import AnalysisCounter from './components/AnalysisCounter';
import WhyDecision from './components/WhyDecision';
import MerchantFingerprint from './components/MerchantFingerprint';
import PipelinePerformance from './components/PipelinePerformance';
import DemoMode from './components/DemoMode';
import { streamWebsiteAnalysis } from './api/client';
import { AlertTriangle } from 'lucide-react';

// ── Hero Stage Mapping ────────────────────────────────────────
const STAGE_STEPS = {
  crawl: 1, extract: 1, prioritize: 1,
  search: 2, candidates: 2,
  vit: 2, logo: 2, reuse: 2, manipulation: 2, identity: 2,
  fusion: 3, completed: 3, all_done: 3,
};

const HERO_HEADLINES = [
  'Does the evidence\nmatch the claim?',
  'Uncovering\nthe truth.',
  'Find out.',
];

export default function App() {
  const [result, setResult]           = useState(null);
  const [loading, setLoading]         = useState(false);
  const [error, setError]             = useState(null);
  const [currentSteps, setCurrentSteps] = useState({});
  const [heroStage, setHeroStage]     = useState(0);
  const [headlineIdx, setHeadlineIdx] = useState(0);
  const [analysisStartTs, setAnalysisStartTs] = useState(null);
  const [analysisEndTs, setAnalysisEndTs]     = useState(null);
  const [feedItems, setFeedItems]     = useState([]);
  // Analyst workflow state (frontend-only, no persistence needed for demo)
  const [analystStatus, setAnalystStatus] = useState(null); // null | 'pending' | 'reviewed' | 'escalated' | 'needs_verification'
  const closeStreamRef = useRef(null);

  const advanceStage = useCallback((stepId) => {
    const targetStage = STAGE_STEPS[stepId] ?? 0;
    setHeroStage(prev => {
      if (targetStage > prev) {
        if (targetStage === 2) setHeadlineIdx(1);
        if (targetStage === 3) setHeadlineIdx(2);
        return targetStage;
      }
      return prev;
    });
  }, []);

  const addFeedItem = useCallback((msg) => {
    if (!msg) return;
    setFeedItems(prev => [
      ...prev.slice(-20),
      { msg, ts: Date.now() },
    ]);
  }, []);

  const handleAnalyze = (url) => {
    if (closeStreamRef.current) closeStreamRef.current();
    setLoading(true);
    setError(null);
    setResult(null);
    setCurrentSteps({});
    setHeroStage(1);
    setHeadlineIdx(0);
    setFeedItems([]);
    setAnalysisStartTs(Date.now());
    setAnalysisEndTs(null);
    setAnalystStatus(null);

    closeStreamRef.current = streamWebsiteAnalysis(
      url,
      (stepEvent) => {
        const stepId = stepEvent.step?.toLowerCase?.() || '';
        setCurrentSteps(prev => ({
          ...prev,
          [stepId]: stepEvent.status || 'completed',
        }));
        advanceStage(stepId);
        if (stepEvent.message) addFeedItem(stepEvent.message);
      },
      (analysisData) => {
        setAnalysisEndTs(Date.now());
        setCurrentSteps(prev => ({ ...prev, all_done: true }));
        advanceStage('all_done');
        setResult(analysisData);
        setLoading(false);
        setAnalystStatus('pending');
      },
      (err) => {
        console.error('Analysis error:', err);
        setAnalysisEndTs(Date.now());
        setError(err.message || 'Analysis failed. Make sure backend is running.');
        setLoading(false);
        setHeroStage(0);
        setHeadlineIdx(0);
      },
    );
  };

  // Demo scenario handler — receives result directly from DemoMode
  const handleDemoResult = (analysisData) => {
    if (closeStreamRef.current) closeStreamRef.current();
    setLoading(false);
    setError(null);
    setResult(analysisData);
    setCurrentSteps({ all_done: true });
    setHeroStage(3);
    setHeadlineIdx(2);
    setAnalysisStartTs(Date.now());
    setAnalysisEndTs(Date.now());
    setAnalystStatus('pending');
    addFeedItem('Demo scenario loaded from deterministic fixture.');
  };

  const PIPELINE_STAGES = [
    { id: 'crawl',    label: 'CRAWL',    steps: ['crawl', 'extract', 'prioritize'] },
    { id: 'discover', label: 'DISCOVER', steps: ['search', 'candidates'] },
    { id: 'verify',   label: 'VERIFY',   steps: ['vit', 'logo', 'reuse', 'manipulation', 'identity'] },
    { id: 'score',    label: 'SCORE',    steps: ['fusion', 'completed'] },
  ];

  const getStageStatus = (stage) => {
    if (currentSteps.all_done) return 'done';
    const anyActive = stage.steps.some(s =>
      currentSteps[s] === 'in_progress' || currentSteps[s] === 'running'
    );
    if (anyActive) return 'active';
    const allDone = stage.steps.some(s =>
      currentSteps[s] === 'completed' || currentSteps[s] === 'done'
    );
    if (allDone) return 'done';
    return 'idle';
  };

  const fusionEvidence = result?.evidence || result?.structured_evidence || result?.candidate_evidence || [];

  // Analyst workflow action labels
  const ANALYST_ACTIONS = [
    { id: 'pending',            label: 'PENDING REVIEW', class: 'tag-amber' },
    { id: 'reviewed',           label: 'REVIEWED',       class: 'tag-green' },
    { id: 'needs_verification', label: 'NEEDS VERIFICATION', class: 'tag-amber' },
    { id: 'escalated',          label: 'ESCALATED',      class: 'tag-red' },
  ];

  return (
    <>
      <a href="#main-content" className="skip-to-content">Skip to main content</a>

      {/* ── Prototype Banner ── */}
      <div className="prototype-banner">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ color: 'var(--amber)', flexShrink: 0 }}>
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
        </svg>
        <span>
          <strong>DECISION-SUPPORT SYSTEM FOR HUMAN RISK ANALYSTS:</strong>{' '}
          This engine produces explainable empirical visual signals to assist risk reviewers.
          It <span style={{ textDecoration: 'underline' }}>never</span> automatically rejects merchants.
        </span>
      </div>

      {/* ── Nav Bar ── */}
      <nav className="nav-bar" aria-label="Main navigation">
        <span className="nav-wordmark">Evidence Engine</span>
        <div className="nav-right">
          <span className="nav-version">v2.4.1</span>
          <button
            className="btn-primary"
            style={{ padding: '0.45rem 1rem', fontSize: '11px' }}
            onClick={() => {
              setResult(null);
              setError(null);
              setHeroStage(0);
              setHeadlineIdx(0);
              setAnalysisStartTs(null);
              setAnalystStatus(null);
            }}
          >
            New Analysis
          </button>
        </div>
      </nav>

      {/* ── Hero ── */}
      <section className="hero-section" aria-label="Hero input">
        <div
          className="hero-bg"
          data-stage={heroStage}
          role="presentation"
          aria-hidden="true"
        />
        <div className="hero-content">
          <span className="eyebrow">Visual Fraud Intelligence</span>

          <div className="hero-headline-wrap" aria-live="polite">
            {HERO_HEADLINES.map((h, i) => (
              <h1
                key={i}
                className={`hero-headline${i === headlineIdx ? ' active' : ''}`}
                aria-hidden={i !== headlineIdx}
              >
                {h}
              </h1>
            ))}
          </div>

          <p style={{ fontFamily: 'Inter', fontSize: '16px', color: 'var(--muted)', maxWidth: '540px', lineHeight: 1.6, marginTop: '-0.25rem' }}>
            Autonomous crawl, visual discovery, and ViT verification for merchant risk underwriting.
          </p>

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

      {/* ── Persistent Analysis Counter ── */}
      <AnalysisCounter
        startTs={analysisStartTs}
        endTs={analysisEndTs}
        loading={loading}
        visible={loading || (result !== null && analysisStartTs !== null)}
      />

      {/* ── Main Content ── */}
      <main id="main-content" className="page-container">

        {/* ── Demo Scenarios (always visible when not loading and no result) ── */}
        {!loading && !result && (
          <div className="section-block" style={{ paddingTop: '2.5rem' }}>
            <div className="section-header" style={{ marginBottom: '1rem' }}>
              <span className="eyebrow">Hackathon Judge Walkthrough</span>
              <h2 className="section-headline">3 Deterministic Demo Scenarios</h2>
              <p className="section-subtext">
                Each scenario runs against a fixed offline fixture — no live external search dependency.
                Results are reproducible and deterministic.
              </p>
            </div>
            <DemoMode onResult={handleDemoResult} loading={loading} />
          </div>
        )}

        {/* ── Error state ── */}
        {error && (
          <div
            className="notice-banner red-notice"
            role="alert"
            style={{ marginTop: '2rem' }}
          >
            <AlertTriangle size={18} color="var(--risk-red)" style={{ flexShrink: 0, marginTop: '2px' }} />
            <div>
              <div className="notice-banner-title">Analysis Notice</div>
              <div className="notice-banner-body">{error}</div>
            </div>
          </div>
        )}

        {/* ── Results ── */}
        {result && (
          <ErrorBoundary onReset={() => { setResult(null); setError(null); }}>

            {/* ── TOP: Risk Verdict ── */}
            <div className="section-block" style={{ paddingTop: '3rem' }}>
              <RiskCards
                fusion={result.fusion}
                claims={result.claims}
                webDetectionMode={result.web_detection_mode}
                webDetectionSimulated={result.web_detection_simulated}
              />
            </div>

            {/* ── Analyst Workflow Status ── */}
            {analystStatus && (
              <div className="card" style={{ marginBottom: '1.5rem', padding: '1rem 1.25rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.75rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
                  <span className="eyebrow" style={{ fontSize: '10px' }}>ANALYST WORKFLOW</span>
                  <span className={`tag ${ANALYST_ACTIONS.find(a => a.id === analystStatus)?.class || 'tag-amber'}`}>
                    {ANALYST_ACTIONS.find(a => a.id === analystStatus)?.label || analystStatus.toUpperCase()}
                  </span>
                </div>
                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                  {ANALYST_ACTIONS.map(a => (
                    <button
                      key={a.id}
                      className="btn-secondary"
                      style={{ padding: '0.3rem 0.8rem', fontSize: '10px', opacity: analystStatus === a.id ? 1 : 0.55 }}
                      onClick={() => setAnalystStatus(a.id)}
                    >
                      {a.label}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* ── WHY THIS DECISION? ── */}
            <WhyDecision
              fusion={result.fusion}
              reuse={result.reuse}
              logo={result.logo}
              manipulation={result.manipulation}
              identity={result.identity}
            />

            {/* ── VISUAL MERCHANT PROFILE ── */}
            <MerchantFingerprint
              reuse={result.reuse}
              logo={result.logo}
              manipulation={result.manipulation}
              identity={result.identity}
              fusion={result.fusion}
            />

            {/* ── PIPELINE PERFORMANCE ── */}
            <PipelinePerformance fusion={result.fusion} result={result} />

            {/* ── CLAIM VS EVIDENCE ── */}
            <div className="section-block">
              <div className="section-header">
                <span className="eyebrow">Claim Analysis Layer</span>
                <h2 className="section-headline">Evidence vs. Claim Reasoning</h2>
                <p className="section-subtext">Does the visual evidence support or contradict what the merchant claims?</p>
              </div>
              <ClaimVsEvidence
                claimsReasoning={result.claims_reasoning}
                structuredEvidence={result.structured_evidence}
                claims={result.claims}
              />
            </div>

            {/* ── EVIDENCE FUSION ── */}
            {fusionEvidence.length > 0 && (
              <div className="section-block">
                <div className="section-header">
                  <span className="eyebrow">Evidence Fusion Layer</span>
                  <h2 className="section-headline">Visual Evidence Exhibits</h2>
                  <p className="section-subtext">
                    Cross-references each extracted asset across public web discovery sources and platform ViT embeddings.
                    {' '}<span style={{ color: 'var(--amber)', fontFamily: 'JetBrains Mono', fontSize: '13px' }}>
                      {fusionEvidence.length} exhibits analyzed
                    </span>
                  </p>
                </div>
                <EvidenceFusionCards evidence={fusionEvidence} />
              </div>
            )}

            {/* ── FORENSIC METRICS ── */}
            <div className="section-block">
              <div className="section-header">
                <span className="eyebrow">Forensic Signal Breakdown</span>
                <h2 className="section-headline">Empirical Visual Metrics</h2>
                <p className="section-subtext">Real-time algorithmic measurements from Vision Transformer embeddings and computer vision filters.</p>
              </div>
              <EvidenceGrid
                reuse={result.reuse}
                logo={result.logo}
                manipulation={result.manipulation}
                identity={result.identity}
              />
            </div>

            {/* ── HEATMAP & DEEP DIVE ── */}
            <div className="section-block">
              <div className="section-header">
                <span className="eyebrow">Forensic Deep-Dive</span>
                <h2 className="section-headline">Analysis Breakdown</h2>
                <p className="section-subtext">Candidate matches, ELA heatmaps, multimodal audit, backbone provenance and raw JSON export.</p>
              </div>
              <HeatmapViewer result={result} />
            </div>

          </ErrorBoundary>
        )}

      </main>

      {/* ── Footer ── */}
      <footer className="site-footer">
        <span className="footer-wordmark">Evidence Engine</span>
        <p className="footer-copy">
          Visual Risk Intelligence · Razorpay AI Risk Manager<br />
          Decision Support — never automatically rejects merchants.
        </p>
      </footer>
    </>
  );
}
