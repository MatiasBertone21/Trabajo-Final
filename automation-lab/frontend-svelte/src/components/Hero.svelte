<section class="hero-panel">
  <div class="hero-copy">
    <p class="eyebrow">Quiet luxury for everyday living</p>
    <h1>Curated essentials for a calmer home.</h1>
    <p>
      Discover sculptural objects, warm textures and everyday pieces designed to feel timeless.
    </p>
    <div class="actions">
      <a class="primary-link" href="/products">Browse collection</a>
      <a class="secondary-link" href="/stories">Our story</a>
    </div>
  </div>

  <aside class="hero-card" aria-label="Featured selection">
    <p class="card-label">This week</p>
    <h2>Stone & Linen Edit</h2>
    <p>Layered neutrals, soft lighting and natural materials.</p>
  </aside>
</section>

<style>
  .hero-panel {
    display: grid;
    grid-template-columns: 1.3fr 0.7fr;
    gap: 1.5rem;
    padding: 2rem;
    border-radius: 2rem;
    background: linear-gradient(135deg, #f8fafc 0%, #eef2ff 100%);
    box-shadow: 0 12px 40px rgba(15, 23, 42, 0.08);
  }

  .hero-copy h1 {
    font-size: clamp(2rem, 4vw, 3.2rem);
    line-height: 1.05;
    margin: 0 0 1rem;
    color: #111827;
  }

  .hero-copy p {
    margin: 0;
    color: #475569;
    max-width: 580px;
    line-height: 1.7;
  }

  .eyebrow {
    text-transform: uppercase;
    letter-spacing: 0.24em;
    font-size: 0.78rem;
    color: #6366f1;
    margin-bottom: 0.8rem;
  }

  .actions {
    display: flex;
    flex-wrap: wrap;
    gap: 0.8rem;
    margin-top: 1.4rem;
  }

  .primary-link,
  .secondary-link {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 0.8rem 1.1rem;
    border-radius: 999px;
    text-decoration: none;
    font-weight: 600;
  }

  .primary-link {
    background: #111827;
    color: white;
  }

  .secondary-link {
    background: white;
    color: #111827;
    border: 1px solid rgba(15, 23, 42, 0.1);
  }

  .hero-card {
    border-radius: 1.5rem;
    padding: 1.4rem;
    background: #111827;
    color: white;
    display: flex;
    flex-direction: column;
    justify-content: end;
    min-height: 220px;
  }

  .card-label {
    text-transform: uppercase;
    letter-spacing: 0.2em;
    font-size: 0.74rem;
    color: #cbd5e1;
    margin-bottom: 0.6rem;
  }

  .hero-card h2 {
    margin: 0 0 0.6rem;
    font-size: 1.45rem;
  }

  .hero-card p {
    margin: 0;
    color: #cbd5e1;
    line-height: 1.6;
  }

  @media (max-width: 780px) {
    .hero-panel {
      grid-template-columns: 1fr;
    }
  }
</style>
