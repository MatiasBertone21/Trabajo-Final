import { Component, OnDestroy, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { cartService } from '../../services/cart.service';
import { Subscription } from 'rxjs';

@Component({
  standalone: true,
  selector: 'cart-page',
  imports: [CommonModule],
  template: `
    <section class="cart-page" [attr.data-testid]="'page-cart'">
      <div class="cart-header">
        <div>
          <p class="eyebrow">Carrito</p>
          <h2>Tu carrito de compras</h2>
        </div>
        <button class="ghost" (click)="clear()" [attr.data-testid]="'cart-clear'">Vaciar carrito</button>
      </div>
      <div class="cart-panel" *ngIf="cart()?.items?.length; else emptyState">
        <div class="cart-list">
          <div class="cart-row" *ngFor="let it of cart().items">
            <div class="item-details">
              <p class="cart-label">{{it.productName}}</p>
              <p class="cart-meta">ID: {{it.productId}}</p>
              <p class="cart-meta">Cantidad: {{it.quantity}}</p>
            </div>
            <div class="item-prices">
              <p class="cart-meta">Precio unitario: $ {{it.unitPrice}}</p>
              <p class="cart-meta">Total: $ {{it.subtotal}}</p>
              <button class="remove" (click)="remove(it.productId)" [attr.data-testid]="'cart-remove-' + it.productId">Quitar</button>
            </div>
          </div>
        </div>
        <div class="cart-summary">
          <p class="summary-title">Resumen</p>
          <p class="summary-item">Total items: <strong>{{cart().totalItems || 0}}</strong></p>
          <p class="summary-item">Total costo: <strong>$ {{cart().totalAmount || 0}}</strong></p>
        </div>
      </div>
      <ng-template #emptyState>
        <div class="empty-state" data-testid="empty-cart">No hay productos en el carrito.</div>
      </ng-template>
    </section>
  `,
  styles: [
    `.cart-page { display: grid; gap: 24px; }
      .cart-header { display: flex; align-items: center; justify-content: space-between; gap: 16px; }
      .eyebrow { margin: 0 0 10px; color: var(--accent); font-size: 0.95rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; }
      h2 { margin: 0; }
      .cart-panel { display: grid; gap: 20px; }
      .cart-list { display: grid; gap: 14px; }
      .cart-row { display: flex; justify-content: space-between; gap: 16px; align-items: center; padding: 18px 22px; border-radius: 22px; background: var(--surface); border: 1px solid rgba(148,163,184,0.16); }
      .item-details { display: grid; gap: 6px; }
      .item-prices { display: grid; gap: 6px; text-align: right; }
      .cart-label { margin: 0 0 6px; font-weight: 700; }
      .cart-meta { margin: 0; color: var(--muted); font-size: 0.95rem; }
      .remove { padding: 10px 16px; border-radius: 16px; background: var(--danger); color: white; }
      .remove:hover { background: #b91c1c; }
      .cart-summary { padding: 24px; border-radius: 24px; background: var(--surface-strong); border: 1px solid rgba(148,163,184,0.12); }
      .summary-title { margin: 0 0 14px; font-weight: 700; color: var(--text); }
      .summary-item { margin: 0 8px 0 0; color: var(--muted); }
      .ghost { padding: 12px 18px; border-radius: 18px; background: transparent; border: 1px solid rgba(79,70,229,0.18); color: var(--text); }
      .empty-state { padding: 24px; border-radius: 24px; border: 1px dashed rgba(148,163,184,0.24); color: var(--muted); text-align: center; }
      @media (max-width: 720px) {
        .cart-row { flex-wrap: wrap; }
      }
    `],})
export class CartPage implements OnInit, OnDestroy {
  cart = signal<any>({ items: [], total: 0 });
  private subscription?: Subscription;

  async ngOnInit() {
    await this.loadCart();
    this.subscription = cartService.cartChanges.subscribe(() => this.loadCart());
  }

  ngOnDestroy() {
    this.subscription?.unsubscribe();
  }

  private async loadCart() {
    this.cart.set(await cartService.getCart());
  }

  async remove(productId: number) {
    this.cart.set(await cartService.removeItem(productId));
  }

  async clear() {
    this.cart.set(await cartService.clear());
  }
}
