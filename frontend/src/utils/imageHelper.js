/**
 * frontend/src/utils/imageHelper.js
 * Safely parses and formats image source strings (data URLs, HTTP URLs, or raw base64)
 */

export function formatImageSrc(imgData) {
  if (!imgData || typeof imgData !== 'string') return null;
  const trimmed = imgData.trim();
  if (trimmed.startsWith('data:image/') || trimmed.startsWith('http://') || trimmed.startsWith('https://') || trimmed.startsWith('/')) {
    return trimmed;
  }
  // If it's a raw base64 string without the data:image prefix
  if (trimmed.length > 20 && !trimmed.includes(' ')) {
    return `data:image/png;base64,${trimmed}`;
  }
  return null;
}
