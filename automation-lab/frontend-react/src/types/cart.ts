export interface CartItem {
  productId: number;
  productName?: string;
  name?: string;
  description?: string;
  unitPrice?: number;
  price?: number;
  quantity: number;
  image?: string;
  subtotal: number;
}

export interface Cart {
  items: CartItem[];
  total?: number;
  totalItems?: number;
  totalAmount?: number;
}
