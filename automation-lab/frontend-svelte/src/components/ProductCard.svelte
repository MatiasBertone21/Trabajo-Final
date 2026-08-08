<script>
  export let product;

  import { addToCart } from '../stores/cart.svelte.js';

  const fallbackImage =
    'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="800" height="500" viewBox="0 0 800 500"%3E%3Cdefs%3E%3ClinearGradient id="g" x1="0" y1="0" x2="1" y2="1"%3E%3Cstop offset="0" stop-color="%23e2e8f0"/%3E%3Cstop offset="1" stop-color="%23cbd5e1"/%3E%3C/linearGradient%3E%3C/defs%3E%3Crect width="800" height="500" fill="url(%23g)"/%3E%3Ctext x="50%25" y="50%25" text-anchor="middle" dominant-baseline="middle" font-family="Arial" font-size="30" fill="%2364758b"%3EProduct image unavailable%3C/text%3E%3C/svg%3E';

  const handleImageError = (event) => {
    event.currentTarget.src = fallbackImage;
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0,
    }).format(value);
  };

  const handleAddToCart = () => {
    addToCart(product);
  };
</script>

<article class="product-card">
  <img src={product.image || fallbackImage} alt={product.name} on:error={handleImageError} />
  <div class="product-body">
    <p class="category">{product.category}</p>
    <h3>{product.name}</h3>
    <p>{product.description}</p>
    <div class="product-meta">
      <strong>{formatCurrency(product.price)}</strong>
      <div class="actions">
        <a class="detail-link" href={`/products/${product.id}`}>View details</a>
        <button type="button" on:click={handleAddToCart}>Add to bag</button>
      </div>
    </div>
  </div>
</article>

<style>
  .product-card {
    border: 1px solid rgba(15, 23, 42, 0.08);
    border-radius: 1.25rem;
    overflow: hidden;
    background: white;
    box-shadow: 0 10px 25px rgba(15, 23, 42, 0.04);
  }

  img {
    display: block;
    width: 100%;
    height: 180px;
    object-fit: cover;
    background: linear-gradient(135deg, #e2e8f0 0%, #cbd5e1 100%);
  }

  .product-body {
    padding: 1rem;
  }

  .category {
    margin: 0 0 0.4rem;
    color: #6366f1;
    text-transform: uppercase;
    letter-spacing: 0.2em;
    font-size: 0.72rem;
  }

  h3 {
    margin: 0 0 0.45rem;
    color: #111827;
  }

  p {
    margin: 0 0 0.8rem;
    color: #64748b;
    line-height: 1.6;
  }

  .product-meta {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.5rem;
  }

  .actions {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .detail-link {
    color: #4338ca;
    font-size: 0.9rem;
    text-decoration: none;
    font-weight: 600;
  }

  strong {
    color: #111827;
  }

  button {
    border: 0;
    background: #111827;
    color: white;
    padding: 0.6rem 0.8rem;
    border-radius: 999px;
    cursor: pointer;
  }
</style>
