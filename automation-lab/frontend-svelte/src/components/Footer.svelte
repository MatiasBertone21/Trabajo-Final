<footer class="site-footer">
  <div>
    <strong>Northstar</strong>
    <p>Modern essentials for a thoughtful home.</p>
  </div>
  <div>
    <strong>Visit</strong>
    <p>42 Harbor Street<br />Lisbon, Portugal</p>
  </div>
  <div>
    <strong>Contact</strong>
    <p>hello@northstar.example<br />+351 212 555 014</p>
  </div>
</footer>

<style>
  .site-footer {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 1rem;
    padding: 2rem 0 0;
    margin-top: 2.2rem;
    border-top: 1px solid rgba(15, 23, 42, 0.08);
    color: #475569;
  }

  .site-footer strong {
    color: #111827;
  }

  .site-footer p {
    margin: 0.4rem 0 0;
    line-height: 1.6;
  }

  @media (max-width: 780px) {
    .site-footer {
      grid-template-columns: 1fr;
    }
  }
</style>
