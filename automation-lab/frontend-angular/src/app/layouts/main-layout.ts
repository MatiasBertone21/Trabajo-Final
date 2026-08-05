import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { Sidebar } from '../components/sidebar/sidebar';
import { Header } from '../components/header/header';

@Component({
  standalone: true,
  selector: 'main-layout',
  template: `
    <app-sidebar></app-sidebar>
    <app-header></app-header>
    <main class="content" [attr.data-testid]="'main-content'">
      <div class="page-shell">
        <router-outlet></router-outlet>
      </div>
    </main>
  `,
  styles: [
    `.content {
        margin-left: 280px;
        padding-top: 90px;
        padding-left: 40px;
        padding-right: 40px;
        min-height: 100vh;
        background: transparent;
      }
      .page-shell {
        max-width: 1280px;
        margin: 0 auto;
        display: grid;
        gap: 26px;
      }
      :host { display: block; }
      @media (max-width: 980px) {
        .content { margin-left: 0; padding-top: 85px; padding-left: 20px; padding-right: 20px; }
      }
    `],
  imports: [Sidebar, Header, RouterOutlet],
})
export class MainLayout {}
