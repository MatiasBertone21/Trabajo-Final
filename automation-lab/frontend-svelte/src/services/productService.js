const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

function resolveImageUrl(image) {
  if (!image) return '';
  if (image.startsWith('http') || image.startsWith('data:')) return image;
  return `${API_BASE_URL.replace(/\/+$/, '')}${image}`;
}

function normalizeProduct(product) {
  if (!product || typeof product !== 'object') return null;
  return {
    id: product.id,
    name: product.name,
    description: product.description,
    price: product.price,
    stock: product.stock,
    category: product.category,
    image: resolveImageUrl(product.image),
  };
}

async function fetchJson(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const message = await response.text();
    const error = new Error(message || 'Unable to load products.');
    error.status = response.status;
    throw error;
  }

  return response.json();
}

export async function getProducts() {
  const data = await fetchJson('/products');
  if (!Array.isArray(data)) return [];
  return data.map(normalizeProduct).filter(Boolean);
}

export async function getProductById(id) {
  try {
    const data = await fetchJson(`/products/${id}`);
    return normalizeProduct(data);
  } catch (error) {
    const isNotFound = error && typeof error === 'object' && error.status === 404;
    if (isNotFound) return null;
    throw error;
  }
}
