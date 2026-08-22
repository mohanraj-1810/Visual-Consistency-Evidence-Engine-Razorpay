/**
 * frontend/src/api/client.js — API client for Visual Consistency Engine backend.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

export async function analyzeWebsiteUrl(url) {
  const res = await fetch(`${API_BASE_URL}/analyze`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ url }),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Analysis failed: ${res.statusText}`);
  }

  return res.json();
}

/**
 * Stream real-time analysis progress using Server-Sent Events (SSE).
 */
export function streamWebsiteAnalysis(url, onStep, onResult, onError) {
  const encodedUrl = encodeURIComponent(url);
  const eventSource = new EventSource(`${API_BASE_URL}/analyze-stream?url=${encodedUrl}`);

  eventSource.onmessage = (event) => {
    try {
      const payload = JSON.parse(event.data);
      if (payload.type === 'step') {
        onStep(payload);
      } else if (payload.type === 'result') {
        onResult(payload.data);
        eventSource.close();
      } else if (payload.type === 'error') {
        onError(new Error(payload.message || 'Analysis stream error'));
        eventSource.close();
      }
    } catch (err) {
      onError(err);
      eventSource.close();
    }
  };

  eventSource.onerror = (err) => {
    // If stream fails, fallback to standard fetch POST
    console.warn('SSE connection interrupted, falling back to POST /analyze', err);
    eventSource.close();
    analyzeWebsiteUrl(url)
      .then(onResult)
      .catch(onError);
  };

  return () => {
    eventSource.close();
  };
}
