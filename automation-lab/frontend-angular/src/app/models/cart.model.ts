export interface CartItem {
  productId: number;
  productName: string;
  description?: string;
  image?: string;
  quantity: number;
  unitPrice: number;
  subtotal: number;
}

export interface CartResponse {
  items: CartItem[];
  totalItems: number;
  totalAmount: number;
}
