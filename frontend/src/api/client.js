/**
 * frontend/src/api/client.js — API client for Visual Consistency Engine backend.
 * Uses Asynchronous WebSocket Job Queue (/api/analyse-merchant + /ws/analysis/{job_id}).
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
const WS_BASE_URL = API_BASE_URL.replace(/^http/, 'ws');

export async function analyzeWebsiteUrl(url) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 120000); // 2 minute timeout

  try {
    const res = await fetch(`${API_BASE_URL}/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
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
      throw new Error('Analysis request timed out after 2 minutes. The target website may be blocking automated scrapers or responding slowly.');
    }
    throw err;
  }
}

/**
 * Stream real-time analysis progress using WebSockets.
 * Submits analysis job to POST /api/analyse-merchant and streams live events via /ws/analysis/{job_id}.
 */
export function streamWebsiteAnalysis(url, onStep, onResult, onError) {
  let isDone = false;
  let socket = null;

  const timeoutTimer = setTimeout(() => {
    if (!isDone) {
      isDone = true;
      if (socket) {
        try { socket.close(); } catch (e) {}
      }
      onError(new Error('Analysis timed out after 2 minutes. The target website may be blocking automated scrapers or responding slowly.'));
    }
  }, 120000);

  // 1. Submit async job to background queue
  fetch(`${API_BASE_URL}/api/analyse-merchant`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
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

      // 2. Connect to WebSocket channel for live updates
      socket = new WebSocket(`${WS_BASE_URL}/ws/analysis/${job_id}`);

      socket.onmessage = (event) => {
        if (isDone) return;
        try {
          const payload = JSON.parse(event.data);

          if (payload.status === 'COMPLETED' && payload.data) {
            isDone = true;
            clearTimeout(timeoutTimer);
            onStep({
              type: 'step',
              step: 'completed',
              label: payload.message || 'Analysis completed',
              status: 'completed',
              message: payload.message,
            });
            onResult(payload.data);
            try { socket.close(); } catch (e) {}
          } else if (payload.status === 'FAILED') {
            isDone = true;
            clearTimeout(timeoutTimer);
            onError(new Error(payload.message || 'Analysis failed.'));
            try { socket.close(); } catch (e) {}
          } else if (payload.type === 'error') {
            isDone = true;
            clearTimeout(timeoutTimer);
            onError(new Error(payload.message || 'WebSocket stream error'));
            try { socket.close(); } catch (e) {}
          } else {
            // Live in-progress step update
            const stepId = (payload.status || 'crawl').toLowerCase();
            onStep({
              type: 'step',
              step: stepId,
              label: payload.message,
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
        console.warn('WebSocket connection error, falling back to direct POST /analyze', err);
        try { socket.close(); } catch (e) {}

        analyzeWebsiteUrl(url)
          .then((data) => {
            if (!isDone) {
              isDone = true;
              clearTimeout(timeoutTimer);
              onResult(data);
            }
          })
          .catch((fallbackErr) => {
            if (!isDone) {
              isDone = true;
              clearTimeout(timeoutTimer);
              onError(fallbackErr);
            }
          });
      };
    })
    .catch((err) => {
      if (isDone) return;
      console.warn('Failed to enqueue job, falling back to POST /analyze', err);
      analyzeWebsiteUrl(url)
        .then((data) => {
          if (!isDone) {
            isDone = true;
            clearTimeout(timeoutTimer);
            onResult(data);
          }
        })
        .catch((fallbackErr) => {
          if (!isDone) {
            isDone = true;
            clearTimeout(timeoutTimer);
            onError(fallbackErr);
          }
        });
    });

  return () => {
    isDone = true;
    clearTimeout(timeoutTimer);
    if (socket) {
      try { socket.close(); } catch (e) {}
    }
  };
}
