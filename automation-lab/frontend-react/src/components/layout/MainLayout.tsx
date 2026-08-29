import { Outlet } from 'react-router-dom';
import { Navbar } from './Navbar';
import { useState, useEffect } from 'react';
import { cartService } from '../../services/cartService';
import styles from '../../styles/App.module.css';

export const MainLayout = () => {
  const [cartCount, setCartCount] = useState(0);

  const fetchCartCount = async () => {
    try {
      const cart = await cartService.getCart();
      const totalItems = cart.items.reduce((acc, item) => acc + item.quantity, 0);
      setCartCount(totalItems);
    } catch {
      setCartCount(0);
    }
  };

  useEffect(() => {
    fetchCartCount();
    window.addEventListener('cartUpdated', fetchCartCount);
    return () => window.removeEventListener('cartUpdated', fetchCartCount);
  }, []);

  return (
    <div className={styles.container}>
      <Navbar cartCount={cartCount} />

      <main data-testid="main-container" className={styles.main}>
        <div className="page-shell">
          <Outlet />
        </div>
      </main>

      <footer data-testid="footer" className={styles.footer + ' footer'}>
        <p>Laboratory Footer</p>
      </footer>
    </div>
  );
}