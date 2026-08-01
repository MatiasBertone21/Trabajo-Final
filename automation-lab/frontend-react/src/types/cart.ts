export interface CartItem {
  productId: number;
  name: string;
  price: number;
  quantity: number;
  image: string;
  subtotal: number;
}

export interface Cart {
  items: CartItem[];
  total: number;
}