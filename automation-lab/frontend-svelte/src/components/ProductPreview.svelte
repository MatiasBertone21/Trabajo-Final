<script>
  import { onMount } from 'svelte';
  import ProductCard from './ProductCard.svelte';
  import { getProducts } from '../services/productService';

  let products = [];
  let loading = true;
  let error = '';

  onMount(async () => {
    try {
      const response = await getProducts();
      products = Array.isArray(response) ? response.slice(0, 3) : [];
      error = '';
    } catch (err) {
      error = 'We could not load the featured products right now.';
      products = [];
    } finally {
      loading = false;
    }
  });
</script>

<section class="preview-section" aria-labelledby="featured-products">
  <div class="section-heading">
    <div>
      <p class="eyebrow">Featured products</p>
      <h2 id="featured-products">Objects that shape the room.</h2>
    </div>
    <a href="/products">See all</a>
  </div>

  {#if loading}
    <div class="state-card">Loading products...</div>
  {:else if error}
    <div class="state-card error">{error}</div>
  {:else if products.length === 0}
    <div class="state-card">No products available at the moment.</div>
  {:else}
    <div class="product-grid">
      {#each products as product}
        <ProductCard {product} />
      {/each}
    </div>
  {/if}
</section>

<style>
  .preview-section {
    padding: 2rem 0 0;
  }

  .section-heading {
    display: flex;
    align-items: end;
    justify-content: space-between;
    gap: 1rem;
    margin-bottom: 1.2rem;
  }

  .section-heading h2 {
    margin: 0;
    color: #111827;
    font-size: 1.4rem;
  }

  .section-heading a {
    color: #6366f1;
    text-decoration: none;
    font-weight: 600;
  }

  .eyebrow {
    margin: 0 0 0.35rem;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.2em;
    font-size: 0.76rem;
  }

  .product-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 1rem;
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

  @media (max-width: 900px) {
    .product-grid {
      grid-template-columns: 1fr;
    }
  }
</style>
