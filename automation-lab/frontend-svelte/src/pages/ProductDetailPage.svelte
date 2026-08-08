<script>
  import { onDestroy } from 'svelte';
  import { getProductById } from '../services/productService';
  import { addToCart } from '../stores/cart.svelte.js';

  export let productId;

  let loading = true;
  let error = '';
  let notFound = false;
  let product = null;
  let cartMessage = '';
  let cartMessageTimeout;

  const fallbackImage =
    'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="1200" height="800" viewBox="0 0 1200 800"%3E%3Cdefs%3E%3ClinearGradient id="g" x1="0" y1="0" x2="1" y2="1"%3E%3Cstop offset="0" stop-color="%23dbeafe"/%3E%3Cstop offset="1" stop-color="%23e2e8f0"/%3E%3C/linearGradient%3E%3C/defs%3E%3Crect width="1200" height="800" fill="url(%23g)"/%3E%3Ctext x="50%25" y="50%25" text-anchor="middle" dominant-baseline="middle" font-family="Arial" font-size="42" fill="%2364758b"%3EImage unavailable%3C/text%3E%3C/svg%3E';

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
    if (!product) return;

    const added = addToCart(product);
    if (!added) return;

    cartMessage = `${product.name} added to cart.`;

    window.clearTimeout(cartMessageTimeout);
    cartMessageTimeout = window.setTimeout(() => {
      cartMessage = '';
    }, 2200);
  };

  const loadProduct = async () => {
    loading = true;
    error = '';
    notFound = false;
    product = null;

    if (!Number.isFinite(productId)) {
      notFound = true;
      loading = false;
      return;
    }

    try {
      const response = await getProductById(productId);
      if (!response) {
        notFound = true;
        product = null;
      } else {
        product = response;
        notFound = false;
      }
      error = '';
    } catch {
      error = 'We could not load this product right now.';
      product = null;
      notFound = false;
    } finally {
      loading = false;
    }
  };

  $: loadProduct(productId);

  onDestroy(() => {
    window.clearTimeout(cartMessageTimeout);
  });
</script>

<section class="detail-page" aria-labelledby="product-detail-title">
  <a class="back-link" href="/products">Back to products</a>

  {#if loading}
    <div class="state-card">Loading product...</div>
  {:else if error}
    <div class="state-card error">{error}</div>
  {:else if notFound}
    <div class="state-card">Product not found.</div>
  {:else if product}
    <article class="detail-card">
      <figure class="media-panel">
        <img src={product.image || fallbackImage} alt={product.name} on:error={handleImageError} />
      </figure>

      <div class="detail-info">
        <p class="category">{product.category}</p>
        <h1 id="product-detail-title">{product.name}</h1>
        <p class="description">{product.description}</p>

        <dl class="meta-list">
          <div>
            <dt>Price</dt>
            <dd>{formatCurrency(product.price)}</dd>
          </div>
          <div>
            <dt>Stock</dt>
            <dd>{product.stock}</dd>
          </div>
        </dl>

        <button type="button" on:click={handleAddToCart}>Add to bag</button>
        {#if cartMessage}
          <p class="cart-feedback" role="status" aria-live="polite">{cartMessage}</p>
        {/if}
      </div>
    </article>
  {/if}
</section>

<style>
  .detail-page {
    display: grid;
    gap: 1rem;
  }

  .back-link {
    justify-self: start;
    color: #4338ca;
    text-decoration: none;
    font-weight: 600;
  }

  .detail-card {
    display: grid;
    grid-template-columns: 1fr 1fr;
    background: white;
    border: 1px solid rgba(15, 23, 42, 0.08);
    border-radius: 1.5rem;
    overflow: hidden;
    box-shadow: 0 10px 25px rgba(15, 23, 42, 0.04);
  }

  .media-panel {
    margin: 0;
    min-height: 320px;
    background: linear-gradient(135deg, #dbeafe, #eff6ff);
  }

  .media-panel img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
  }

  .detail-info {
    padding: 1.5rem;
    display: grid;
    gap: 1rem;
  }

  .category {
    margin: 0;
    color: #6366f1;
    text-transform: uppercase;
    letter-spacing: 0.2em;
    font-size: 0.72rem;
  }

  h1 {
    margin: 0;
    color: #111827;
    font-size: clamp(1.8rem, 3vw, 2.5rem);
  }

  .description {
    margin: 0;
    color: #64748b;
    line-height: 1.65;
  }

  .meta-list {
    margin: 0;
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 1rem;
  }

  .meta-list dt {
    color: #64748b;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
  }

  .meta-list dd {
    margin: 0.35rem 0 0;
    color: #111827;
    font-weight: 700;
  }

  button {
    width: fit-content;
    border: 0;
    background: #111827;
    color: white;
    padding: 0.7rem 1rem;
    border-radius: 999px;
    cursor: pointer;
  }

  .cart-feedback {
    margin: 0;
    color: #0f766e;
    background: #ecfeff;
    border: 1px solid #99f6e4;
    padding: 0.55rem 0.7rem;
    border-radius: 0.65rem;
    font-weight: 600;
    font-size: 0.9rem;
  }

  .state-card {
    padding: 1rem 1.1rem;
    border-radius: 1rem;
    background: white;
    color: #334155;
    border: 1px solid rgba(15, 23, 42, 0.08);
  }

  .state-card.error {
    color: #b91c1c;
    background: #fef2f2;
  }

  @media (max-width: 860px) {
    .detail-card {
      grid-template-columns: 1fr;
    }

    .media-panel {
      min-height: 240px;
    }
  }
</style>
