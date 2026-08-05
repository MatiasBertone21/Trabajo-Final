import { Component, OnDestroy, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, ActivatedRoute, RouterLink } from '@angular/router';
import { Subscription } from 'rxjs';
import { productService } from '../../services/product.service';

@Component({
  standalone: true,
  selector: 'app-sidebar',
  imports: [CommonModule, RouterLink],
  template: `
    <aside class="sidebar" [attr.data-testid]="'sidebar-categories'">
      <div class="brand-box">
        <span class="brand-mark">RB</span>
        <div>
          <h3 class="brand">Rabbit Bazaar</h3>
          <p class="brand-tag">Tienda minimalista</p>
        </div>
      </div>
      <nav class="main-nav" aria-label="Main navigation">
        <a routerLink="/" [attr.data-testid]="'sidebar-home'">Inicio</a>
        <a routerLink="/products" [attr.data-testid]="'sidebar-products'">Catálogo</a>
      </nav>
      <section class="categories">
        <div class="section-header">
          <h4>Categorías</h4>
        </div>
        <ul>
          <li *ngFor="let c of categories(); let i = index" [class.selected-category]="c === selectedCategory()">
            <a href="#" (click)="selectCategory(c); $event.preventDefault()" [attr.data-testid]="'category-' + c">{{c}}</a>
          </li>
          <li *ngIf="selectedCategory()" class="clear-category">
            <button class="clear" (click)="clearCategory()" [attr.data-testid]="'clear-category'">Borrar filtro</button>
          </li>
        </ul>
      </section>
    </aside>
  `,
  styles: [
    `.sidebar {
        width: 280px;
        min-height: 100vh;
        padding: 28px 22px;
        background: rgba(255,255,255,0.95);
        border-right: 1px solid rgba(148,163,184,0.18);
        position: fixed;
        inset: 0 auto 0 0;
        overflow-y: auto;
        box-shadow: inset -1px 0 0 rgba(148,163,184,0.12);
      }
      .brand-box {
        display: flex;
        align-items: center;
        gap: 14px;
        margin-bottom: 32px;
      }
      .brand-mark {
        width: 48px;
        height: 48px;
        display: grid;
        place-items: center;
        border-radius: 16px;
        background: var(--accent-soft);
        color: var(--accent);
        font-weight: 800;
        letter-spacing: -0.04em;
      }
      .brand { margin: 0; font-size: 1.2rem; letter-spacing: -0.02em; }
      .brand-tag { margin: 6px 0 0; color: var(--muted); font-size: 0.95rem; }
      .main-nav {
        display: flex;
        flex-direction: column;
        gap: 10px;
        margin-bottom: 28px;
      }
      .main-nav a {
        display: inline-flex;
        align-items: center;
        gap: 10px;
        padding: 12px 16px;
        border-radius: 14px;
        background: #f8f9ff;
        color: var(--text);
        font-weight: 600;
        border: 1px solid transparent;
      }
      .main-nav a:hover,
      .main-nav a:focus-visible {
        border-color: rgba(79,70,229,0.18);
        background: rgba(79,70,229,0.08);
      }
      .categories {
        padding: 18px 0 12px;
      }
      .section-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
      }
      .categories h4 { margin: 0; font-size: 0.98rem; color: var(--text); }
      .categories ul {
        list-style: none;
        padding: 0;
        margin: 0;
        display: grid;
        gap: 10px;
      }
      .categories li {
        display: flex;
        align-items: center;
        justify-content: space-between;
        border-radius: 14px;
        background: var(--surface-strong);
        border: 1px solid rgba(148,163,184,0.12);
      }
      .categories a {
        display: block;
        padding: 12px 14px;
        color: var(--text);
        font-size: 0.96rem;
        flex: 1;
      }
      .categories a:hover,
      .categories a:focus-visible {
        background: var(--accent-soft);
        color: var(--accent);
      }
      .selected-category a {
        font-weight: 700;
        color: var(--accent);
      }
      .clear {
        border: none;
        background: transparent;
        color: var(--muted);
        font-size: 1.1rem;
        padding: 0 16px;
        cursor: pointer;
      }
      .clear:hover,
      .clear:focus-visible {
        color: var(--danger);
      }
      @media (max-width: 980px) {
        .sidebar { position: relative; width: 100%; height: auto; border-right: none; box-shadow: none; }
      }
    `],
})
export class Sidebar implements OnInit, OnDestroy {
  categories = signal<string[]>([]);
  selectedCategory = signal<string | null>(null);
  private subscription?: Subscription;

  constructor(private router: Router, private route: ActivatedRoute) {}

  async ngOnInit() {
    try {
      const cats = await productService.categories();
      this.categories.set(cats);
    } catch (e) {
      this.categories.set([]);
    }

    this.subscription = this.route.queryParams.subscribe((params) => {
      this.selectedCategory.set(params['category'] || null);
    });
  }

  selectCategory(category: string) {
    this.router.navigate(['/products'], { queryParams: { category } });
  }

  clearCategory() {
    this.router.navigate(['/products'], { queryParams: {} });
  }

  ngOnDestroy() {
    this.subscription?.unsubscribe();
  }
}
