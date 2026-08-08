<script>
  import { onMount } from 'svelte';
  import ProductCard from '../components/ProductCard.svelte';
  import { getProducts } from '../services/productService';

  let products = [];
  let loading = true;
  let error = '';

  onMount(async () => {
    try {
      const response = await getProducts();
      products = Array.isArray(response) ? response : [];
      error = '';
    } catch {
      error = 'We could not load the catalog right now.';
      products = [];
    } finally {
      loading = false;
    }
  });
</script>

<section class="products-page" aria-labelledby="products-heading">
  <header class="page-header">
    <p class="eyebrow">Catalog</p>
    <h1 id="products-heading">All products</h1>
    <p>Browse the complete selection available in the Automation Lab store.</p>
  </header>

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
  .products-page {
    display: grid;
    gap: 1.25rem;
  }

  .page-header h1 {
    margin: 0 0 0.5rem;
    color: #111827;
    font-size: clamp(1.8rem, 2.5vw, 2.4rem);
  }

  .page-header p {
    margin: 0;
    color: #64748b;
    line-height: 1.6;
    max-width: 60ch;
  }

  .eyebrow {
    margin: 0 0 0.45rem;
    color: #6366f1;
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

  @media (max-width: 960px) {
    .product-grid {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
  }

  @media (max-width: 700px) {
    .product-grid {
      grid-template-columns: 1fr;
    }
  }
</style>
