import { Subject } from 'rxjs';
import { apiFetch } from '../core/api.client';
import type { CartResponse } from '../models/cart.model';

export class CartService {
  cartChanges = new Subject<void>();

  async getCart(): Promise<CartResponse> {
    return apiFetch('/cart/');
  }

  async addItem(productId: number, quantity = 1): Promise<CartResponse> {
    const result = await apiFetch('/cart/items', {
      method: 'POST',
      body: JSON.stringify({ productId, quantity }),
    });
    this.cartChanges.next();
    return result;
  }

  async updateItem(productId: number, quantity: number): Promise<CartResponse> {
    const result = await apiFetch(`/cart/items/${productId}?quantity=${quantity}`, {
      method: 'PUT',
    });
    this.cartChanges.next();
    return result;
  }

  async removeItem(productId: number): Promise<CartResponse> {
    const result = await apiFetch(`/cart/items/${productId}`, { method: 'DELETE' });
    this.cartChanges.next();
    return result;
  }

  async clear(): Promise<CartResponse> {
    const result = await apiFetch('/cart/', { method: 'DELETE' });
    this.cartChanges.next();
    return result;
  }
}

export const cartService = new CartService();
