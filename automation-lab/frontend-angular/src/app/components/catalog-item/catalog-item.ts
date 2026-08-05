import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import type { Product } from '../../models/product.model';
import { RouterLink } from '@angular/router';

@Component({
  standalone: true,
  selector: 'catalog-item',
  imports: [CommonModule, RouterLink],
  template: `
    <article class="catalog-card" [attr.data-testid]="'catalog-item-' + (product?.id ?? '')">
      <div class="card-inner">
        <a [routerLink]="['/products', product?.id]" class="catalog-link">
          <div class="media">
            <img *ngIf="product?.image" [src]="product?.image" [attr.alt]="product?.title" />
          </div>
          <div class="content">
            <h3>{{product?.title}}</h3>
            <div class="meta">
              <span class="category">{{product?.category}}</span>
              <span class="stock" [attr.data-testid]="'stock-' + product?.id">{{product?.stock ?? 0}} disponible</span>
            </div>
            <div class="row">
              <span class="price">$ {{ product?.price }}</span>
            </div>
          </div>
        </a>
        <div class="actions">
          <button class="add" (click)="addToCart($event)" [attr.data-testid]="'catalog-add-' + product?.id">Agregar</button>
        </div>
      </div>
    </article>
  `,
  styles: [
    `.catalog-card {
        background: var(--surface);
        border: 1px solid rgba(148,163,184,0.16);
        border-radius: 22px;
        overflow: hidden;
        box-shadow: var(--shadow);
        transition: transform 0.25s ease, border-color 0.25s ease;
      }
      .catalog-card:hover {
        transform: translateY(-3px);
        border-color: rgba(79,70,229,0.2);
      }
      .catalog-link {
        display: grid;
        grid-template-rows: auto 1fr;
        height: 100%;
        color: inherit;
        text-decoration: none;
      }
      .media {
        min-height: 180px;
        background: var(--surface-strong);
      }
      .media img {
        width: 100%;
        height: 180px;
        object-fit: cover;
      }
      .content {
        padding: 18px 16px 20px;
      }
      h3 {
        margin: 0 0 10px;
        font-size: 1rem;
        line-height: 1.3;
      }
      .price {
        display: inline-flex;
        align-items: center;
        border-radius: 999px;
        padding: 8px 12px;
        background: var(--accent-soft);
        color: var(--accent);
        font-weight: 700;
      }
      .card-inner {
        display: grid;
        gap: 14px;
      }
      .actions {
        padding: 0 16px 16px;
      }
      .add {
        width: 100%;
        border: none;
        border-radius: 16px;
        padding: 14px 16px;
        background: var(--accent);
        color: #fff;
        font-weight: 700;
        cursor: pointer;
      }
      .add:hover,
      .add:focus-visible {
        background: #4338ca;
      }
    `],
})
export class CatalogItem {
  @Input({ required: true }) product?: Product;

  async addToCart(e: Event) {
    e.preventDefault();
    // lazy import to avoid cycles and preserve existing cartService
    const { cartService } = await import('../../services/cart.service');
    if (!this.product) return;
    await cartService.addItem(this.product.id, 1);
    alert('Añadido al carrito');
  }
}
