import { Component, OnInit, signal } from '@angular/core';
import { CommonModule, Location } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { productService } from '../../services/product.service';
import { cartService } from '../../services/cart.service';

@Component({
  standalone: true,
  selector: 'product-detail',
  imports: [CommonModule],
  template: `
    <section class="detail-page" [attr.data-testid]="'page-product-detail'">
      <button class="back" (click)="goBack()" [attr.data-testid]="'back-button'">← Volver</button>
      <div *ngIf="product(); else notFound" class="detail-card">
        <div class="media-panel">
          <img *ngIf="product().image" [src]="product().image" [attr.alt]="product().title" />
        </div>
        <div class="detail-info">
          <div class="detail-badge">Producto destacado</div>
          <h1>{{product().title}}</h1>
          <p class="detail-description">{{product().description}}</p>
          <div class="detail-actions">
            <span class="detail-price">$ {{ product().price }}</span>
            <button (click)="addToCart()" [attr.data-testid]="'add-to-cart'">Agregar al carrito</button>
          </div>
        </div>
      </div>
      <ng-template #notFound>
        <div class="empty-state" data-testid="product-not-found">Producto no encontrado</div>
      </ng-template>
    </section>
  `,
  styles: [
    `.detail-page { display: grid; gap: 26px; }
      .detail-card {
        display: grid;
        grid-template-columns: 1fr 1.1fr;
        gap: 28px;
        background: var(--surface);
        border: 1px solid rgba(148,163,184,0.14);
        border-radius: 28px;
        box-shadow: var(--shadow);
        overflow: hidden;
      }
      .media-panel { min-height: 420px; background: var(--surface-strong); display: grid; place-items: center; }
      .media-panel img { width: 100%; height: 100%; object-fit: cover; }
      .detail-info { padding: 34px; display: grid; gap: 24px; }
      .detail-badge { display: inline-flex; padding: 10px 14px; border-radius: 999px; background: var(--accent-soft); color: var(--accent); font-weight: 700; font-size: 0.85rem; }
      h1 { margin: 0; font-size: clamp(2rem, 2.5vw, 2.6rem); line-height: 1.05; }
      .detail-description { margin: 0; color: var(--muted); max-width: 42rem; }
      .detail-actions { display: flex; flex-wrap: wrap; gap: 16px; align-items: center; }
      .detail-price {
        font-size: 1.6rem;
        font-weight: 800;
        color: var(--accent);
      }
      button { padding: 14px 24px; border-radius: 18px; background: var(--accent); color: #fff; font-weight: 700; }
      button:hover { background: #4338ca; }
      @media (max-width: 880px) {
        .detail-card { grid-template-columns: 1fr; }
      }
    `],})
export class ProductDetailPage implements OnInit {
  product = signal<any | null>(null);

  constructor(private route: ActivatedRoute, private location: Location) {}

  async ngOnInit() {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    try {
      const p = await productService.get(id);
      this.product.set(p);
    } catch {
      this.product.set(null);
    }
  }

  async addToCart() {
    if (!this.product()) return;
    await cartService.addItem(this.product().id, 1);
    alert('Añadido al carrito');
  }

  goBack() {
    this.location.back();
  }
}
