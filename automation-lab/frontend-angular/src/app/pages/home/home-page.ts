import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { productService } from '../../services/product.service';
import { CatalogItem } from '../../components/catalog-item/catalog-item';

@Component({
  standalone: true,
  selector: 'home-page',
  imports: [CommonModule, CatalogItem],
  template: `
    <section class="home-page" [attr.data-testid]="'page-home'">
      <div class="hero-card">
        <div>
          <p class="eyebrow">Rabbit Bazaar</p>
          <h1>Descubre productos únicos con una experiencia fluida.</h1>
          <p class="hero-copy">Navega por la tienda con una interfaz limpia y cómoda, diseñada para enfocarte en lo que importa.</p>
        </div>
      </div>
      <div class="grid">
        <catalog-item *ngFor="let p of products()" [product]="p"></catalog-item>
      </div>
    </section>
  `,
  styles: [
    `.home-page {
        display: grid;
        gap: 28px;
      }
      .hero-card {
        background: var(--surface);
        border: 1px solid rgba(148,163,184,0.14);
        border-radius: 28px;
        padding: 30px 34px;
        box-shadow: var(--shadow);
      }
      .eyebrow {
        margin: 0 0 10px;
        color: var(--accent);
        font-size: 0.95rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }
      h1 {
        margin: 0;
        font-size: clamp(2rem, 2.25vw, 2.9rem);
        line-height: 1.05;
      }
      .hero-copy {
        margin: 18px 0 0;
        max-width: 660px;
        color: var(--muted);
      }
      .grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
        gap: 24px;
      }
      @media (max-width: 720px) {
        .hero-card { padding: 24px; }
      }
    `],
})
export class HomePage implements OnInit {
  products = signal<any[]>([]);

  async ngOnInit() {
    try {
      const list = await productService.list();
      this.products.set(list || []);
    } catch (e) {
      this.products.set([]);
    }
  }
}
