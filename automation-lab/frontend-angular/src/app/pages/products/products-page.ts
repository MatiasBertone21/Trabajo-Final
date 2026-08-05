import { Component, OnDestroy, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { CatalogItem } from '../../components/catalog-item/catalog-item';
import { productService } from '../../services/product.service';
import { ActivatedRoute } from '@angular/router';
import { Subscription } from 'rxjs';

@Component({
  standalone: true,
  selector: 'products-page',
  imports: [CommonModule, CatalogItem],
  template: `
    <section class="products-page" [attr.data-testid]="'page-products'">
      <div class="section-header">
        <div>
          <p class="eyebrow">Catálogo</p>
          <h2>Explora nuestros productos</h2>
        </div>
        <div class="search-bar">
          <input
            type="search"
            [value]="searchTerm()"
            (input)="onSearch($event)"
            placeholder="Buscar productos..."
            aria-label="Buscar productos"
            data-testid="product-search"
          />
        </div>
      </div>
      <div class="grid">
        <catalog-item *ngFor="let p of products(); trackBy: trackById" [product]="p"></catalog-item>
      </div>
    </section>
  `,
  styles: [
    `.products-page { display: grid; gap: 28px; }
      .section-header { display: flex; align-items: center; justify-content: space-between; gap: 20px; flex-wrap: wrap; }
      .eyebrow { margin: 0 0 10px; color: var(--accent); font-size: 0.95rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; }
      h2 { margin: 0; font-size: clamp(1.7rem, 2vw, 2.4rem); }
      .search-bar { min-width: 280px; width: 100%; max-width: 420px; }
      .search-bar input {
        width: 100%;
        padding: 12px 16px;
        border-radius: 16px;
        border: 1px solid rgba(148,163,184,0.22);
        background: var(--surface-strong);
        color: var(--text);
        font-size: 0.95rem;
      }
      .search-bar input:focus {
        outline: none;
        border-color: rgba(79,70,229,0.5);
        box-shadow: 0 0 0 3px rgba(79,70,229,0.08);
      }
      .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 24px; }
    `],})
export class ProductsPage implements OnInit, OnDestroy {
  products = signal<any[]>([]);
  searchTerm = signal('');
  private allProducts: any[] = [];
  private currentCategory: string | null = null;
  private subscription?: Subscription;

  trackById(_: number, item: any) {
    return item?.id;
  }

  constructor(private route: ActivatedRoute) {}

  async ngOnInit() {
    try {
      this.allProducts = await productService.list();
      this.subscription = this.route.queryParamMap.subscribe((params) => {
        this.currentCategory = params.get('category');
        this.applyFilters();
      });
      this.applyFilters();
    } catch {
      this.products.set([]);
    }
  }

  ngOnDestroy() {
    this.subscription?.unsubscribe();
  }

  onSearch(event: Event) {
    const value = (event.target as HTMLInputElement).value || '';
    this.searchTerm.set(value);
    this.applyFilters();
  }

  private applyFilters() {
    const term = this.searchTerm().trim().toLowerCase();
    let filtered = this.allProducts;

    if (this.currentCategory) {
      filtered = filtered.filter((x: any) => x.category === this.currentCategory);
    }

    if (term) {
      filtered = filtered.filter((product: any) => {
        const title = String(product.title || product.name || '').toLowerCase();
        const description = String(product.description || '').toLowerCase();
        const category = String(product.category || '').toLowerCase();
        return title.includes(term) || description.includes(term) || category.includes(term);
      });
    }

    this.products.set(filtered);
  }
}
