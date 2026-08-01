import { Link, useNavigate } from 'react-router-dom';

interface NavbarProps {
  cartCount?: number;
}

export const Navbar = ({ cartCount = 0 }: NavbarProps) => {
  const navigate = useNavigate();
  const user = localStorage.getItem('user');

  const handleLogout = () => {
    localStorage.removeItem('user');
    navigate('/login');
  };

  return (
    <nav className="panel" style={{ padding: '0.9rem 1.2rem', display: 'flex', flexWrap: 'wrap', gap: '1rem', alignItems: 'center', justifyContent: 'space-between' }}>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem', alignItems: 'center' }}>
        <Link to="/" data-testid="navbar-home" className="button-secondary">Home</Link>
        <Link to="/products" data-testid="navbar-products" className="button-secondary">Products</Link>
        <Link to="/cart" data-testid="navbar-cart" className="button-secondary">
          Carrito (<span data-testid="cart-counter">{cartCount}</span>)
        </Link>
      </div>

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem', alignItems: 'center' }}>
        {user ? (
          <>
            <span style={{ color: 'var(--text)', fontWeight: 500 }}>Hola, {user}</span>
            <button onClick={handleLogout} data-testid="navbar-logout" className="button-secondary">Logout</button>
          </>
        ) : (
          <Link to="/login" data-testid="navbar-login" className="button-primary">Login</Link>
        )}
      </div>
    </nav>
  );
};