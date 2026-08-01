import type { Product } from '../../types/product';
import { cartService } from '../../services/cartService';
import { getImageUrl } from '../../utils/image';

export const ProductCard = ({ product }: { product: Product }) => {
    const handleAddToCart = async () => {
      try {
        await cartService.addItem(product.id, 1);
        window.dispatchEvent(new Event('cartUpdated'));
        alert("Producto agregado al carrito");
      } catch {
        alert("Error al agregar producto");
      }
    };

  return (
    <div data-testid="product-card" className="product-card">
      <img
        src={getImageUrl((product as any).image)}
        alt={product.name}
        style={{ width: '100%', height: '160px', objectFit: 'cover', borderRadius: '12px' }}
        data-testid="product-image"
      />

      <div style={{ display: 'flex', justifyContent: 'space-between', gap: '0.75rem', alignItems: 'baseline' }}>
        <h3 data-testid="product-name">{product.name}</h3>
        <span className="product-price">${product.price}</span>
      </div>

      <p style={{ color: 'var(--muted)', margin: 0 }}>{product.category}</p>
      <p style={{ color: 'var(--muted)', marginTop: '0.25rem' }}>Stock: {product.stock}</p>

      <div style={{ marginTop: 'auto' }}>
        <button type="button" onClick={handleAddToCart} data-testid="add-to-cart-button" className="button-primary">
          Agregar al carrito
        </button>
      </div>
    </div>
  );
};