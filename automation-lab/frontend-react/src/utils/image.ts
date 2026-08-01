// Utility to build full image URLs for product assets.
// Uses VITE_API_BASE_URL when available and falls back to a safe placeholder.

const PLACEHOLDER_SVG = `data:image/svg+xml;utf8,${encodeURIComponent(
  `<svg xmlns='http://www.w3.org/2000/svg' width='600' height='400' viewBox='0 0 600 400'>
     <rect width='100%' height='100%' fill='%23f3f4f6' />
     <g fill='%239ca3af' font-family='system-ui, -apple-system, BlinkMacSystemFont, \"Segoe UI\", Roboto, sans-serif' font-size='20'>
       <text x='50%' y='50%' dominant-baseline='middle' text-anchor='middle'>No image</text>
     </g>
  </svg>`
)}
`;

export function getImageUrl(relativePath?: string | null): string {
  try {
    const base = typeof import.meta !== 'undefined' && (import.meta as any).env?.VITE_API_BASE_URL
      ? String((import.meta as any).env.VITE_API_BASE_URL).replace(/\/+$/, '')
      : '';

    if (!relativePath) return PLACEHOLDER_SVG;

    const trimmed = String(relativePath).trim();
    if (!trimmed) return PLACEHOLDER_SVG;

    // If it's already an absolute URL, return as-is
    if (/^https?:\/\//i.test(trimmed)) return trimmed;

    // Ensure leading slash for path
    const path = trimmed.startsWith('/') ? trimmed : `/${trimmed}`;

    // If base exists, join; otherwise return the path so the browser will request relative URL
    return base ? `${base}${path}` : path;
  } catch (e) {
    return PLACEHOLDER_SVG;
  }
}

export default getImageUrl;
