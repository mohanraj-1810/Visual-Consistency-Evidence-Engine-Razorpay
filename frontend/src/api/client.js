/**
 * frontend/src/api/client.js — API client for Visual Consistency Engine backend.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

export async function fetchDemoCases() {
  const res = await fetch(`${API_BASE_URL}/demo-cases`);
  if (!res.ok) {
    throw new Error(`Failed to fetch demo cases: ${res.statusText}`);
  }
  return res.json();
}

export async function analyzeMerchant(formData) {
  const res = await fetch(`${API_BASE_URL}/analyze`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Analysis failed: ${res.statusText}`);
  }

  return res.json();
}
