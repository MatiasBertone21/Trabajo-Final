import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { authService } from '../../core/auth.service';

@Component({
  standalone: true,
  selector: 'app-header',
  imports: [CommonModule, RouterLink],
  template: `
    <header class="app-header">
      <div class="inner-header">
        <a routerLink="/" class="logo" [attr.data-testid]="'header-logo'">
          <strong>Rabbit</strong><span>Bazaar</span>
        </a>
        <nav class="header-nav" aria-label="Secondary navigation">
          <a routerLink="/products" [attr.data-testid]="'header-products'">Productos</a>
          <a routerLink="/cart" [attr.data-testid]="'sidebar-cart'">Carrito</a>
          <a *ngIf="!isAuth()" routerLink="/login" [attr.data-testid]="'header-login'">Ingresar</a>
          <button *ngIf="isAuth()" class="ghost" (click)="logout()" [attr.data-testid]="'header-logout'">Salir</button>
        </nav>
      </div>
    </header>
  `,
  styles: [
    `.app-header {
        position: fixed;
        left: 280px;
        right: 0;
        top: 0;
        height: 70px;
        display: flex;
        align-items: center;
        padding: 0 28px;
        background: rgba(255,255,255,0.92);
        border-bottom: 1px solid rgba(148,163,184,0.12);
        backdrop-filter: blur(12px);
        z-index: 10;
      }
      .inner-header {
        width: 100%;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 24px;
      }
      .logo {
        display: inline-flex;
        align-items: baseline;
        gap: 8px;
        font-weight: 800;
        color: var(--accent);
        font-size: 1.2rem;
      }
      .logo strong {
        letter-spacing: -0.05em;
      }
      .logo span {
        color: var(--text);
        font-size: 0.95rem;
        font-weight: 500;
      }
      .header-nav {
        display: flex;
        flex-wrap: wrap;
        gap: 14px;
        align-items: center;
      }
      .header-nav a,
      .header-nav .ghost {
        padding: 12px 18px;
        border-radius: 999px;
        font-weight: 600;
        color: var(--text);
        background: var(--surface-strong);
      }
      .header-nav a:hover,
      .header-nav .ghost:hover {
        background: var(--accent-soft);
        color: var(--accent);
      }
      .ghost {
        background: transparent;
        border: 1px solid rgba(79,70,229,0.12);
      }
      @media (max-width: 980px) {
        .app-header { left: 0; padding: 0 18px; }
      }
    `],
})
export class Header {
  isAuth() { return authService.isAuthenticated(); }

  logout() { authService.logout(); }
}
