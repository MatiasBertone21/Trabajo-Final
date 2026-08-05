import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { authService } from '../../core/auth.service';

@Component({
  standalone: true,
  selector: 'login-page',
  imports: [CommonModule, FormsModule, RouterModule],
  template: `
    <section class="login-shell" [attr.data-testid]="'page-login'">
      <div class="login-card">
        <div class="login-hero">
          <span class="login-mark">RB</span>
          <h2>Bienvenido a Rabbit Bazaar</h2>
          <p>Ingresa con tus credenciales para continuar comprando.</p>
        </div>
        <form class="login-form" (ngSubmit)="submit()">
          <label>
            Email
            <input type="email" name="email" [(ngModel)]="email" [attr.data-testid]="'login-email'" required />
          </label>
          <label>
            Contraseña
            <input type="password" name="password" [(ngModel)]="password" [attr.data-testid]="'login-password'" required />
          </label>
          <button type="submit" [attr.data-testid]="'login-submit'">Entrar</button>
        </form>
      </div>
    </section>
  `,
  styles: [
    `.login-shell {
        min-height: calc(100vh - 90px);
        display: grid;
        place-items: center;
        padding: 60px 0;
      }
      .login-card {
        width: min(100%, 460px);
        background: var(--surface);
        border: 1px solid rgba(148,163,184,0.16);
        border-radius: 28px;
        box-shadow: var(--shadow);
        overflow: hidden;
      }
      .login-hero {
        padding: 32px 28px 24px;
        background: var(--accent-soft);
      }
      .login-mark {
        display: inline-flex;
        width: 44px;
        height: 44px;
        align-items: center;
        justify-content: center;
        border-radius: 16px;
        background: var(--accent);
        color: white;
        font-weight: 700;
        margin-bottom: 18px;
      }
      .login-hero h2 {
        margin: 0 0 8px;
        font-size: 1.6rem;
      }
      .login-hero p {
        margin: 0;
        color: var(--muted);
      }
      .login-form {
        display: grid;
        gap: 18px;
        padding: 28px;
      }
      label {
        display: grid;
        gap: 8px;
        font-weight: 600;
        color: var(--text);
      }
      input {
        width: 100%;
        border: 1px solid rgba(148,163,184,0.24);
        border-radius: 16px;
        padding: 14px 16px;
        background: var(--surface-strong);
        color: var(--text);
      }
      input:focus {
        border-color: rgba(79,70,229,0.3);
      }
      button {
        width: 100%;
        padding: 14px 18px;
        border-radius: 16px;
        background: var(--accent);
        color: white;
        font-weight: 700;
        box-shadow: 0 14px 24px rgba(79,70,229,0.14);
      }
      button:hover {
        background: #4338ca;
      }
    `],
})
export class LoginPage {
  email = '';
  password = '';
  constructor(private router: Router) {}

  async submit() {
    try {
      await authService.login(this.email, this.password);
      this.router.navigate(['/']);
    } catch (e) {
      alert('Credenciales inválidas');
    }
  }
}
