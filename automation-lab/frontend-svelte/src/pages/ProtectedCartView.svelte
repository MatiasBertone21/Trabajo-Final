<script>
  import CartPage from './CartPage.svelte';
  import LoginPage from './LoginPage.svelte';
  import { authToken } from '../stores/auth.svelte.js';
</script>

{#if $authToken}
  <CartPage />
{:else}
  <LoginPage redirectTo="/cart" />
{/if}