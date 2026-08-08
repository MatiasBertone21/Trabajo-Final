<script>
  import { onMount } from 'svelte';
  import Navbar from './components/Navbar.svelte';
  import HomePage from './pages/HomePage.svelte';
  import ProductsPage from './pages/ProductsPage.svelte';
  import ProductDetailPage from './pages/ProductDetailPage.svelte';
  import ProtectedCartView from './pages/ProtectedCartView.svelte';
  import LoginPage from './pages/LoginPage.svelte';
  import Footer from './components/Footer.svelte';

  const AUTH_TOKEN_KEY = 'automation_lab_auth_token';

  let currentPath = window.location.pathname;

  const PRODUCT_DETAIL_PATTERN = /^\/products\/(\d+)\/?$/;

  const navigate = (path) => {
    if (path === currentPath) return;
    window.history.pushState({}, '', path);
    currentPath = path;
  };

  const handlePopState = () => {
    currentPath = window.location.pathname;
  };

  const handleNavigation = (event) => {
    if (event.defaultPrevented) return;
    if (event.button !== 0) return;
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    if (!(event.target instanceof Element)) return;

    const anchor = event.target.closest('a');
    if (!anchor) return;
    if (anchor.target && anchor.target !== '_self') return;

    const href = anchor.getAttribute('href');
    if (!href || !href.startsWith('/')) return;

    event.preventDefault();
    navigate(href);
  };

  onMount(() => {
    if (window.location.pathname === '/cart' && !window.localStorage.getItem(AUTH_TOKEN_KEY)) {
      window.history.replaceState({}, '', '/login?redirect=/cart');
      currentPath = '/login';
    }
  });

  const resolveRoute = (path) => {
    if (path === '/') {
      return { name: 'home' };
    }

    if (path === '/products') {
      return { name: 'products' };
    }

    if (path === '/login') {
      return { name: 'login' };
    }

    if (path === '/cart') {
      return { name: 'cart' };
    }

    const match = path.match(PRODUCT_DETAIL_PATTERN);
    if (match) {
      return {
        name: 'product-detail',
        productId: Number(match[1]),
      };
    }

    return { name: 'not-found' };
  };

  $: route = resolveRoute(currentPath);

  $: if (currentPath === '/cart' && !window.localStorage.getItem(AUTH_TOKEN_KEY)) {
    window.history.replaceState({}, '', '/login?redirect=/cart');
    currentPath = '/login';
  }

</script>

<svelte:head>
  <title>Northstar | Modern essentials</title>
</svelte:head>

<svelte:window on:popstate={handlePopState} on:click={handleNavigation} />

<div class="page-shell">
  <Navbar />

  <main class="content">
    {#if route.name === 'home'}
      <HomePage />
    {:else if route.name === 'products'}
      <ProductsPage />
    {:else if route.name === 'product-detail'}
      <ProductDetailPage productId={route.productId} />
    {:else if route.name === 'cart'}
      <ProtectedCartView />
    {:else if route.name === 'login'}
      <LoginPage />
    {:else}
      <section class="not-found">
        <h1>Page not found</h1>
        <p>The page you requested is not available.</p>
        <a href="/products">Back to products</a>
      </section>
    {/if}
  </main>

  <Footer />
</div>

<style>
  :global(body) {
    margin: 0;
    font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: #f8fafc;
    color: #0f172a;
  }

  :global(*) {
    box-sizing: border-box;
  }

  :global(a) {
    transition: opacity 0.2s ease;
  }

  :global(a:hover) {
    opacity: 0.9;
  }

  .page-shell {
    min-height: 100vh;
    padding: 0 1.25rem 2rem;
    max-width: 1280px;
    margin: 0 auto;
  }

  .content {
    padding: 1.5rem 0 0;
  }

  .not-found {
    padding: 1.5rem;
    border-radius: 1rem;
    background: white;
    border: 1px solid rgba(15, 23, 42, 0.08);
  }

  .not-found h1 {
    margin: 0 0 0.6rem;
    color: #111827;
  }

  .not-found p {
    margin: 0 0 0.7rem;
    color: #64748b;
  }

  .not-found a {
    color: #4338ca;
    text-decoration: none;
    font-weight: 600;
  }
</style>
