<script>
  import { login } from '../stores/auth.svelte.js';
  import { navigateTo } from '../utils/navigation.js';

  export let onSuccess = () => {};
  export let redirectTo = '/';

  let email = '';
  let password = '';
  let loading = false;
  let error = '';

  const getRedirectTarget = () => {
    if (typeof window === 'undefined') return '/';

    const params = new URLSearchParams(window.location.search);
    const redirect = params.get('redirect');
    if (redirect && redirect.startsWith('/')) {
      return redirect;
    }

    return redirectTo;
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    loading = true;
    error = '';

    try {
      await login(email.trim(), password);
      onSuccess();
      navigateTo(getRedirectTarget());
    } catch (caughtError) {
      error = 'Credenciales inválidas. Intenta de nuevo.';
    } finally {
      loading = false;
    }
  };
</script>

<section class="login-shell" aria-labelledby="login-heading">
  <div class="login-card">
    <div class="login-hero">
      <span class="login-mark">NS</span>
      <h1 id="login-heading">Sign in</h1>
      <p>Use your email and password to continue.</p>
    </div>

    <form class="login-form" on:submit={handleSubmit}>
      <label>
        <span>Email</span>
        <input bind:value={email} type="email" name="email" autocomplete="email" required />
      </label>

      <label>
        <span>Password</span>
        <input bind:value={password} type="password" name="password" autocomplete="current-password" required />
      </label>

      {#if error}
        <p class="form-error" role="alert">{error}</p>
      {/if}

      <button type="submit" disabled={loading}>
        {loading ? 'Signing in...' : 'Enter'}
      </button>
    </form>
  </div>
</section>

<style>
  .login-shell {
    min-height: calc(100vh - 12rem);
    display: grid;
    place-items: center;
    padding: 2rem 0;
  }

  .login-card {
    width: min(100%, 460px);
    overflow: hidden;
    border-radius: 1.5rem;
    border: 1px solid rgba(15, 23, 42, 0.08);
    background: white;
    box-shadow: 0 14px 34px rgba(15, 23, 42, 0.08);
  }

  .login-hero {
    padding: 1.5rem;
    background: linear-gradient(135deg, #eff6ff, #e0f2fe);
  }

  .login-mark {
    display: inline-grid;
    place-items: center;
    width: 2.75rem;
    height: 2.75rem;
    border-radius: 0.9rem;
    background: #111827;
    color: white;
    font-weight: 800;
    margin-bottom: 1rem;
  }

  .login-hero h1 {
    margin: 0 0 0.45rem;
    color: #111827;
  }

  .login-hero p {
    margin: 0;
    color: #64748b;
    line-height: 1.6;
  }

  .login-form {
    display: grid;
    gap: 1rem;
    padding: 1.5rem;
  }

  label {
    display: grid;
    gap: 0.45rem;
    color: #334155;
    font-weight: 600;
  }

  input {
    width: 100%;
    border-radius: 0.9rem;
    border: 1px solid rgba(15, 23, 42, 0.14);
    padding: 0.85rem 0.95rem;
    background: #fff;
    color: #0f172a;
  }

  input:focus {
    outline: 2px solid rgba(59, 130, 246, 0.18);
    outline-offset: 2px;
  }

  .form-error {
    margin: 0;
    color: #b91c1c;
    background: #fef2f2;
    border: 1px solid #fecaca;
    border-radius: 0.8rem;
    padding: 0.7rem 0.85rem;
  }

  button {
    border: 0;
    border-radius: 0.95rem;
    padding: 0.9rem 1rem;
    background: #111827;
    color: white;
    font-weight: 700;
    cursor: pointer;
  }

  button:disabled {
    cursor: wait;
    opacity: 0.7;
  }
</style>
