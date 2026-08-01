import { apiClient } from '../api/axiosConfig';
import type { Cart } from '../types/cart';

export const cartService = {
  getCart: async (): Promise<Cart> => {
    const { data } = await apiClient.get('/cart');
    return data;
  },

  addItem: async (productId: number, quantity: number = 1): Promise<Cart> => {
    const { data } = await apiClient.post('/cart/items', { productId, quantity });
    return data;
  },

  updateItem: async (productId: number, quantity: number): Promise<Cart> => {
    const { data } = await apiClient.put(`/cart/items/${productId}`, null, {
        params: { quantity }
        });    
    return data;
  },

  removeItem: async (productId: number): Promise<Cart> => {
    const { data } = await apiClient.delete(`/cart/items/${productId}`);
    return data;
  },

  clearCart: async (): Promise<void> => {
    await apiClient.delete('/cart');
  }
};