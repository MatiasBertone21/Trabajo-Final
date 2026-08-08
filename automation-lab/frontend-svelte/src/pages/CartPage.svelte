<script>
  import {
    cartDisplayItems,
    cartQuantity,
    cartTotal,
    incrementItem,
    decrementItem,
    removeFromCart,
  } from '../stores/cart.svelte.js';

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 2,
    }).format(value);
  };
</script>

<section class="cart-page" aria-labelledby="cart-heading">
  <header class="cart-header">
    <div>
      <p class="eyebrow">Cart</p>
      <h1 id="cart-heading">Your bag</h1>
      <p>Review your items before continuing to checkout in a future stage.</p>
    </div>
    {#if $cartDisplayItems.length > 0}
      <p class="unit-counter">{$cartQuantity} {$cartQuantity === 1 ? 'unit' : 'units'}</p>
    {/if}
  </header>

  {#if $cartDisplayItems.length === 0}
    <section class="empty-cart" aria-live="polite">
      <h2>Your cart is empty</h2>
      <p>Browse the catalog and add products to start building your order.</p>
      <a href="/products">Go to products</a>
    </section>
  {:else}
    <div class="cart-layout">
      <div class="cart-list" role="list" aria-label="Cart items">
        {#each $cartDisplayItems as item (item.id)}
          <article class="cart-item" role="listitem">
            <img src={item.image} alt={item.name} />

            <div class="item-details">
              <h2>{item.name}</h2>
              <p class="item-price">{formatCurrency(item.price)} each</p>
              <p class="item-subtotal">Subtotal: {formatCurrency(item.subtotal)}</p>
            </div>

            <div class="item-controls" aria-label={`Quantity controls for ${item.name}`}>
              <button type="button" on:click={() => decrementItem(item.id)} aria-label={`Decrease quantity for ${item.name}`}>
                -
              </button>
              <span>{item.quantity}</span>
              <button type="button" on:click={() => incrementItem(item.id)} aria-label={`Increase quantity for ${item.name}`}>
                +
              </button>
            </div>

            <button class="remove-button" type="button" on:click={() => removeFromCart(item.id)}>
              Remove
            </button>
          </article>
        {/each}
      </div>

      <aside class="cart-summary" aria-label="Cart summary">
        <h2>Order summary</h2>
        <p>
          <span>Total items</span>
          <strong>{$cartQuantity}</strong>
        </p>
        <p>
          <span>Total</span>
          <strong>{formatCurrency($cartTotal)}</strong>
        </p>
      </aside>
    </div>
  {/if}
</section>

<style>
  .cart-page {
    display: grid;
    gap: 1.25rem;
  }

  .cart-header {
    display: flex;
    align-items: end;
    justify-content: space-between;
    gap: 1rem;
    flex-wrap: wrap;
  }

  .eyebrow {
    margin: 0 0 0.45rem;
    color: #6366f1;
    text-transform: uppercase;
    letter-spacing: 0.2em;
    font-size: 0.76rem;
  }

  h1 {
    margin: 0 0 0.5rem;
    color: #111827;
    font-size: clamp(1.8rem, 2.5vw, 2.4rem);
  }

  .cart-header p {
    margin: 0;
    color: #64748b;
    line-height: 1.6;
    max-width: 60ch;
  }

  .unit-counter {
    margin: 0;
    border-radius: 999px;
    background: #111827;
    color: white;
    padding: 0.55rem 0.95rem;
    font-weight: 600;
  }

  .empty-cart {
    border: 1px dashed rgba(15, 23, 42, 0.2);
    background: white;
    border-radius: 1rem;
    padding: 1.25rem;
    display: grid;
    gap: 0.8rem;
  }

  .empty-cart h2,
  .empty-cart p {
    margin: 0;
  }

  .empty-cart a {
    justify-self: start;
    color: #4338ca;
    text-decoration: none;
    font-weight: 600;
  }

  .cart-layout {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 1rem;
    align-items: start;
  }

  .cart-list {
    display: grid;
    gap: 0.8rem;
  }

  .cart-item {
    display: grid;
    grid-template-columns: 110px 1fr auto auto;
    gap: 1rem;
    align-items: center;
    border: 1px solid rgba(15, 23, 42, 0.08);
    border-radius: 1rem;
    background: white;
    padding: 0.8rem;
  }

  .cart-item img {
    width: 110px;
    height: 90px;
    object-fit: cover;
    border-radius: 0.65rem;
    background: linear-gradient(135deg, #e2e8f0 0%, #cbd5e1 100%);
  }

  .item-details h2 {
    margin: 0 0 0.3rem;
    font-size: 1rem;
    color: #111827;
  }

  .item-price,
  .item-subtotal {
    margin: 0;
    color: #64748b;
    font-size: 0.92rem;
  }

  .item-subtotal {
    margin-top: 0.2rem;
    color: #1e293b;
    font-weight: 600;
  }

  .item-controls {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    border: 1px solid rgba(15, 23, 42, 0.12);
    border-radius: 999px;
    padding: 0.25rem;
  }

  .item-controls button {
    border: 0;
    width: 1.8rem;
    height: 1.8rem;
    border-radius: 999px;
    background: #e2e8f0;
    color: #0f172a;
    cursor: pointer;
    font-weight: 700;
  }

  .item-controls span {
    min-width: 1.1rem;
    text-align: center;
    color: #0f172a;
    font-weight: 600;
  }

  .remove-button {
    border: 0;
    background: #fee2e2;
    color: #b91c1c;
    border-radius: 999px;
    padding: 0.45rem 0.75rem;
    cursor: pointer;
    font-weight: 600;
  }

  .cart-summary {
    border: 1px solid rgba(15, 23, 42, 0.08);
    border-radius: 1rem;
    background: white;
    padding: 1rem;
    display: grid;
    gap: 0.65rem;
  }

  .cart-summary h2 {
    margin: 0 0 0.35rem;
    font-size: 1.1rem;
    color: #111827;
  }

  .cart-summary p {
    margin: 0;
    display: flex;
    align-items: center;
    justify-content: space-between;
    color: #334155;
  }

  @media (max-width: 980px) {
    .cart-layout {
      grid-template-columns: 1fr;
    }
  }

  @media (max-width: 760px) {
    .cart-item {
      grid-template-columns: 1fr;
      align-items: start;
    }

    .cart-item img {
      width: 100%;
      height: 180px;
    }

    .item-controls {
      justify-self: start;
    }

    .remove-button {
      justify-self: start;
    }
  }
</style>
