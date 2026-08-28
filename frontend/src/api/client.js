/**
 * frontend/src/api/client.js — API client for Visual Consistency Engine backend.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

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
 * Stream real-time analysis progress using Server-Sent Events (SSE).
 */
export function streamWebsiteAnalysis(url, onStep, onResult, onError) {
  let isDone = false;
  const encodedUrl = encodeURIComponent(url);
  const eventSource = new EventSource(`${API_BASE_URL}/analyze-stream?url=${encodedUrl}`);

  const timeoutTimer = setTimeout(() => {
    if (!isDone) {
      isDone = true;
      try {
        eventSource.close();
      } catch (e) {}
      onError(new Error('Analysis timed out after 2 minutes. Try a specific product URL or check if the backend server is running on http://127.0.0.1:8000.'));
    }
  }, 120000);

  eventSource.onmessage = (event) => {
    if (isDone) return;
    try {
      const payload = JSON.parse(event.data);
      if (payload.type === 'step') {
        onStep(payload);
      } else if (payload.type === 'result') {
        isDone = true;
        clearTimeout(timeoutTimer);
        onResult(payload.data);
        eventSource.close();
      } else if (payload.type === 'error') {
        isDone = true;
        clearTimeout(timeoutTimer);
        onError(new Error(payload.message || 'Analysis stream error'));
        eventSource.close();
      }
    } catch (err) {
      console.error('Failed to parse SSE payload:', err);
    }
  };

  eventSource.onerror = (err) => {
    if (isDone) return;
    console.warn('SSE connection interrupted, falling back to POST /analyze', err);
    try {
      eventSource.close();
    } catch (e) {}

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

  return () => {
    isDone = true;
    clearTimeout(timeoutTimer);
    try {
      eventSource.close();
    } catch (e) {}
  };
}
