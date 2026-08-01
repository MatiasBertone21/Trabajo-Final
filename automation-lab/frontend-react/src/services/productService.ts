import { apiClient } from '../api/axiosConfig'; 
import type { Product } from '../types/product';

export const productService = {
  getAll: async (): Promise<Product[]> => {
    const response = await apiClient.get('/products');
    return response.data;
  },
  getCategories: async (): Promise<string[]> => {
    const response = await apiClient.get('/categories');
    return response.data;
  }
};