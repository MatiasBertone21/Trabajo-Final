export interface CartItem {
  productId: number;
  productName: string;
  quantity: number;
  unitPrice: number;
  subtotal: number;
}

export interface CartResponse {
  items: CartItem[];
  totalItems: number;
  totalAmount: number;
}
