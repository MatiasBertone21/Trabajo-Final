<script>
  import { cartQuantity } from '../stores/cart.svelte.js';
  import { authUser, isAuthenticated, logout } from '../stores/auth.svelte.js';
  import { navigateTo } from '../utils/navigation.js';

  const links = [
    { label: 'Products', href: '/products' },
    { label: 'Stories', href: '/stories' },
    { label: 'Journal', href: '/journal' }
  ];

  const handleLogout = () => {
    logout();
    navigateTo('/login');
  };
</script>

<header class="topbar">
  <a class="brand" href="/" aria-label="Northstar home">
    <span class="brand-mark">N</span>
    <span>Northstar</span>
  </a>

  <nav class="nav-links" aria-label="Primary">
    {#each links as link}
      <a href={link.href}>{link.label}</a>
    {/each}
  </nav>

  <div class="topbar-actions">
    {#if $isAuthenticated}
      <span class="user-chip">{$authUser?.email}</span>
      <button class="text-link button-link" type="button" on:click={handleLogout}>Logout</button>
    {:else}
      <a class="text-link" href="/login">Login</a>
    {/if}
    <a class="cart-pill" href="/cart" aria-label="View cart">
      <span>Cart</span>
      <strong>{$cartQuantity}</strong>
    </a>
  </div>
</header>

<style>
  .topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    padding: 1rem 1.5rem;
    border-bottom: 1px solid rgba(15, 23, 42, 0.08);
    background: rgba(255, 255, 255, 0.82);
    backdrop-filter: blur(14px);
    position: sticky;
    top: 0;
    z-index: 5;
  }

  .brand {
    display: inline-flex;
    align-items: center;
    gap: 0.75rem;
    font-weight: 700;
    color: #111827;
    text-decoration: none;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    font-size: 0.95rem;
  }

  .brand-mark {
    display: inline-grid;
    place-items: center;
    width: 2.1rem;
    height: 2.1rem;
    border-radius: 999px;
    background: linear-gradient(135deg, #111827, #64748b);
    color: white;
    font-size: 0.95rem;
  }

  .nav-links {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
  }

  .nav-links a,
  .text-link {
    color: #334155;
    text-decoration: none;
    font-size: 0.95rem;
  }

  .topbar-actions {
    display: flex;
    align-items: center;
    gap: 0.85rem;
  }

  .user-chip {
    color: #0f172a;
    font-size: 0.92rem;
    font-weight: 600;
  }

  .cart-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.55rem;
    padding: 0.6rem 0.85rem;
    border-radius: 999px;
    background: #111827;
    color: white;
    text-decoration: none;
  }

  .cart-pill strong {
    display: inline-grid;
    place-items: center;
    min-width: 1.4rem;
    height: 1.4rem;
    padding: 0 0.2rem;
    border-radius: 999px;
    background: #f59e0b;
    color: #111827;
    font-size: 0.78rem;
  }

  .button-link {
    border: 0;
    background: transparent;
    cursor: pointer;
    padding: 0;
  }

  @media (max-width: 780px) {
    .topbar {
      flex-wrap: wrap;
      justify-content: center;
    }

    .nav-links {
      justify-content: center;
      width: 100%;
      order: 3;
    }
  }
</style>
