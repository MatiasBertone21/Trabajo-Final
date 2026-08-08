import { writable, derived } from 'svelte/store';

const roundCurrency = (value) => {
  return Math.round((value + Number.EPSILON) * 100) / 100;
};

const toNumber = (value, fallback = 0) => {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
};

const normalizeProduct = (product) => {
  if (!product || typeof product !== 'object') return null;

  const id = toNumber(product.id, NaN);
  if (!Number.isFinite(id)) return null;

  return {
    id,
    name: String(product.name || 'Product'),
    price: toNumber(product.price, 0),
    image: String(product.image || ''),
  };
};

export const cartItems = writable([]);

export const cartQuantity = derived(cartItems, ($cartItems) => {
  return $cartItems.reduce((total, item) => total + item.quantity, 0);
});

export const cartTotal = derived(cartItems, ($cartItems) => {
  return roundCurrency($cartItems.reduce((total, item) => total + item.price * item.quantity, 0));
});

export const cartState = derived([cartItems, cartQuantity, cartTotal], ([$cartItems, $cartQuantity, $cartTotal]) => {
  return {
    cartItems: $cartItems,
    quantity: $cartQuantity,
    total: $cartTotal,
  };
});

export const cartDisplayItems = derived(cartItems, ($cartItems) => {
  return $cartItems.map((item) => ({
    ...item,
    subtotal: roundCurrency(item.price * item.quantity),
  }));
});

export const addToCart = (product) => {
  const normalized = normalizeProduct(product);
  if (!normalized) return false;

  let added = false;

  cartItems.update((items) => {
    const nextItems = [...items];
    const existing = nextItems.find((item) => item.id === normalized.id);

    if (existing) {
      existing.quantity += 1;
    } else {
      nextItems.push({
        ...normalized,
        quantity: 1,
      });
    }

    added = true;
    return nextItems;
  });

  return added;
};

export const incrementItem = (productId) => {
  const id = toNumber(productId, NaN);
  if (!Number.isFinite(id)) return;

  cartItems.update((items) => {
    return items.map((item) => {
      if (item.id !== id) return item;
      return {
        ...item,
        quantity: item.quantity + 1,
      };
    });
  });
};

export const decrementItem = (productId) => {
  const id = toNumber(productId, NaN);
  if (!Number.isFinite(id)) return;

  cartItems.update((items) => {
    return items.reduce((nextItems, item) => {
      if (item.id !== id) {
        nextItems.push(item);
        return nextItems;
      }

      if (item.quantity <= 1) {
        return nextItems;
      }

      nextItems.push({
        ...item,
        quantity: item.quantity - 1,
      });

      return nextItems;
    }, []);
  });
};

export const removeFromCart = (productId) => {
  const id = toNumber(productId, NaN);
  if (!Number.isFinite(id)) return;

  cartItems.update((items) => items.filter((item) => item.id !== id));
};

export const clearCart = () => {
  cartItems.set([]);
};
