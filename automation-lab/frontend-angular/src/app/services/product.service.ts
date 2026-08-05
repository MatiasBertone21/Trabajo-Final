import { apiFetch, API_BASE } from '../core/api.client';
import type { Product } from '../models/product.model';

function resolveImageUrl(image?: string) {
  if (!image) return undefined;
  // backend exposes images under /assets, ensure absolute URL to API
  if (image.startsWith('http') || image.startsWith('data:')) return image;
  return API_BASE.replace(/\/$/, '') + image;
}

export class ProductService {
  async list(): Promise<Product[]> {
    const raw = await apiFetch('/products');
    const items = Array.isArray(raw) ? raw : (raw?.value ?? raw?.items ?? []);
    return (items || []).map((p: any) => ({
      id: p.id,
      title: p.name || p.title,
      description: p.description,
      price: p.price,
      category: p.category,
      image: resolveImageUrl(p.image),
      stock: p.stock,
    } as Product));
  }

  async get(id: number): Promise<Product | null> {
    const p = await apiFetch(`/products/${id}`);
    if (!p) return null;
    const item = Array.isArray(p) ? p[0] : (p?.value ?? p);
    return {
      id: item.id,
      title: item.name || item.title,
      description: item.description,
      price: item.price,
      category: item.category,
      image: resolveImageUrl(item.image),
      stock: item.stock,
    } as Product;
  }

  async categories(): Promise<string[]> {
    return apiFetch('/categories');
  }
}

export const productService = new ProductService();
