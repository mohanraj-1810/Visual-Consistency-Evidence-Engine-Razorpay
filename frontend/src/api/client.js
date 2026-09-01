/**
 * frontend/src/api/client.js — API client for Visual Consistency Engine backend.
 * Uses Asynchronous WebSocket Job Queue (/api/analyse-merchant + /ws/analysis/{job_id}).
 *
 * In development: requests go through Vite proxy → http://127.0.0.1:8000
 * In production:  VITE_API_URL env var points directly to the backend host.
 */

// In dev the Vite proxy handles /api and /ws on the same origin.
// In production set VITE_API_URL=https://your-backend.com
const API_BASE_URL = import.meta.env.VITE_API_URL || '';

// Derive WebSocket base: empty string means same-origin (proxy handles it in dev).
// For production VITE_API_URL set, replace http(s) with ws(s).
const WS_BASE_URL = API_BASE_URL
  ? API_BASE_URL.replace(/^https/, 'wss').replace(/^http/, 'ws')
  : '';   // empty → same origin, browser fills it in

/**
 * Direct synchronous analysis (fallback when WS/job queue is unavailable).
 */
export async function analyzeWebsiteUrl(url) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 120000);

  try {
    const res = await fetch(`${API_BASE_URL}/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url }),
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      throw new Error(errorData.detail || `Analysis failed: ${res.statusText}`);
    }
    return await res.json();
  } catch (err) {
    clearTimeout(timeoutId);
    if (err.name === 'AbortError') {
      throw new Error(
        'Analysis request timed out after 2 minutes. The target website may be blocking automated scrapers or responding slowly.'
      );
    }
    throw err;
  }
}

/**
 * Stream real-time analysis progress using WebSockets.
 * POST /api/analyse-merchant  → get job_id
 * WS   /ws/analysis/{job_id}  → stream live progress events
 *
 * Falls back to POST /analyze on WS failure.
 *
 * @param {string}   url       Merchant website URL
 * @param {Function} onStep    Called with each progress event  { step, status, message }
 * @param {Function} onResult  Called once with the final result payload
 * @param {Function} onError   Called with an Error on failure
 * @returns {Function}         cleanup function — call to cancel the stream
 */
export function streamWebsiteAnalysis(url, onStep, onResult, onError) {
  let isDone = false;
  let socket = null;

  const timeoutTimer = setTimeout(() => {
    if (!isDone) {
      isDone = true;
      if (socket) { try { socket.close(); } catch (_) {} }
      onError(new Error(
        'Analysis timed out after 2 minutes. The target website may be blocking automated scrapers or responding slowly.'
      ));
    }
  }, 120000);

  // ── Step 1: Enqueue the job ──────────────────────────────────────────────
  fetch(`${API_BASE_URL}/api/analyse-merchant`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      merchant_id: `merchant_${Date.now()}`,
      website_url: url,
    }),
  })
    .then(async (res) => {
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to enqueue analysis: ${res.statusText}`);
      }
      return res.json();
    })
    .then(({ job_id }) => {
      if (isDone) return;

      // ── Step 2: Open WebSocket for live progress ────────────────────────
      // Build the WS URL. In dev (API_BASE_URL='') use same-origin with ws/wss.
      const wsProtocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
      const wsHost = WS_BASE_URL || `${wsProtocol}://${window.location.host}`;
      socket = new WebSocket(`${wsHost}/ws/analysis/${job_id}`);

      socket.onmessage = (event) => {
        if (isDone) return;
        try {
          const payload = JSON.parse(event.data);

          if (payload.status === 'COMPLETED' && payload.data) {
            isDone = true;
            clearTimeout(timeoutTimer);
            onStep({ type: 'step', step: 'fusion', status: 'completed', message: payload.message });
            onResult(payload.data);
            try { socket.close(); } catch (_) {}

          } else if (payload.status === 'FAILED') {
            isDone = true;
            clearTimeout(timeoutTimer);
            onError(new Error(payload.message || 'Analysis failed.'));
            try { socket.close(); } catch (_) {}

          } else if (payload.type === 'error') {
            isDone = true;
            clearTimeout(timeoutTimer);
            onError(new Error(payload.message || 'WebSocket stream error'));
            try { socket.close(); } catch (_) {}

          } else {
            // In-progress step event
            // Map backend status strings to the step IDs HeroInput expects
            const statusToStep = {
              CRAWLING:             'crawl',
              EXTRACTING_IMAGES:    'extract',
              SEARCHING_WEB:        'search',
              ANALYSING_FORENSICS:  'forensics',
              SCORING:              'fusion',
            };
            const stepId = statusToStep[payload.status] || (payload.status || 'crawl').toLowerCase();
            onStep({
              type: 'step',
              step: stepId,
              status: 'in_progress',
              message: payload.message,
            });
          }
        } catch (err) {
          console.error('Failed to parse WebSocket payload:', err);
        }
      };

      socket.onerror = (err) => {
        if (isDone) return;
        console.warn('WebSocket error, falling back to POST /analyze', err);
        try { socket.close(); } catch (_) {}
        _fallbackAnalyze(url, isDone, timeoutTimer, onResult, onError, (done) => { isDone = done; });
      };

      socket.onclose = (ev) => {
        // Unexpected close before we got a result
        if (!isDone && ev.code !== 1000) {
          console.warn('WebSocket closed unexpectedly, falling back to POST /analyze');
          _fallbackAnalyze(url, isDone, timeoutTimer, onResult, onError, (done) => { isDone = done; });
        }
      };
    })
    .catch((err) => {
      if (isDone) return;
      console.warn('Failed to enqueue job, falling back to POST /analyze', err);
      _fallbackAnalyze(url, isDone, timeoutTimer, onResult, onError, (done) => { isDone = done; });
    });

  // Return cleanup function
  return () => {
    isDone = true;
    clearTimeout(timeoutTimer);
    if (socket) { try { socket.close(); } catch (_) {} }
  };
}

/** Internal: fallback to synchronous /analyze when WS is unavailable */
function _fallbackAnalyze(url, isDone, timeoutTimer, onResult, onError, setDone) {
  if (isDone) return;
  analyzeWebsiteUrl(url)
    .then((data) => {
      if (!isDone) {
        setDone(true);
        clearTimeout(timeoutTimer);
        onResult(data);
      }
    })
    .catch((fallbackErr) => {
      if (!isDone) {
        setDone(true);
        clearTimeout(timeoutTimer);
        onError(fallbackErr);
      }
    });
}
