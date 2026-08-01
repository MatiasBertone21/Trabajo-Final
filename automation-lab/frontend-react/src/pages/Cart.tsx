import { useState, useEffect } from 'react';
import { cartService } from '../services/cartService';
import { getImageUrl } from '../utils/image';
import type { Cart as CartType } from '../types/cart';

export const Cart = () => {
  const [cart, setCart] = useState<CartType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const fetchCart = async () => {
    try {
      setLoading(true);
      const data = await cartService.getCart();
      setCart(data);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCart();
  }, []);

  const notifyCartChange = () => {
    window.dispatchEvent(new Event('cartUpdated'));
  };

  const handleUpdateQuantity = async (productId: number, quantity: number) => {
    if (quantity <= 0) return handleRemove(productId);
    try {
      const updated = await cartService.updateItem(productId, quantity);
      setCart(updated);
      notifyCartChange();
    } catch {
      alert("Error al actualizar la cantidad");
    }
  };

  const handleRemove = async (productId: number) => {
    try {
      const updated = await cartService.removeItem(productId);
      setCart(updated);
      notifyCartChange();
    } catch {
      alert("Error al eliminar el producto");
    }
  };

  const handleClear = async () => {
    try {
      await cartService.clearCart();
      setCart({ items: [], total: 0 });
      notifyCartChange();
    } catch {
      alert("Error al vaciar el carrito");
    }
  };

  if (loading) return <div data-testid="loading-state" className="status-message">Cargando carrito...</div>;
  if (error) return <div data-testid="error-state" className="status-message">Error al cargar el carrito.</div>;
  if (!cart || cart.items.length === 0) return <div data-testid="empty-cart" className="empty-state">Tu carrito está vacío.</div>;

  return (
    <div data-testid="cart-page" className="cart-page">
      <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem', alignItems: 'center' }}>
        <div>
          <h2>Tu Carrito de Compras</h2>
          <p className="page-copy">Revisa y actualiza las unidades antes de finalizar tu compra.</p>
        </div>
        <button onClick={handleClear} data-testid="clear-cart-button" className="button-secondary">Vaciar Carrito</button>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {cart.items.map((item) => {
            const itemSubtotal = item.subtotal ?? (item.price * item.quantity);

          return (
            <div key={item.productId} data-testid="cart-item" className="cart-item">
              <img src={getImageUrl(item.image)} alt={item.name} />

              <div className="cart-item-details">
                <div className="cart-item-header">
                  <div>
                    <h4 data-testid="cart-item-name">{item.name}</h4>
                    <p style={{ color: 'var(--muted)' }}>Precio: ${item.price}</p>
                  </div>
                  <span style={{ fontWeight: 700, color: 'var(--text-h)' }}>Subtotal: <span data-testid="cart-item-subtotal">${itemSubtotal}</span></span>
                </div>

                <div className="cart-item-actions">
                  <div className="quantity-control">
                    <button type="button" onClick={() => handleUpdateQuantity(item.productId, item.quantity - 1)} data-testid="decrease-quantity" className="button-secondary">-</button>
                    <span data-testid="cart-item-quantity">{item.quantity}</span>
                    <button type="button" onClick={() => handleUpdateQuantity(item.productId, item.quantity + 1)} data-testid="increase-quantity" className="button-secondary">+</button>
                  </div>
                  <button type="button" onClick={() => handleRemove(item.productId)} data-testid="remove-item-button" className="button-danger">Eliminar</button>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="cart-summary">
        Total: $<span data-testid="cart-total">{cart.total > 0 ? cart.total : cart.items.reduce((acc, i) => acc + (i.subtotal ?? (i.price * i.quantity)), 0)}</span>
      </div>
    </div>
  );
};