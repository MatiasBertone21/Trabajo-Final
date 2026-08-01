import { Routes, Route } from 'react-router-dom';
import { MainLayout } from '../components/layout/MainLayout';
import { Home } from '../pages/Home';
import { Login } from '../pages/Login';
import { Products } from '../pages/Products';
import { Cart } from '../pages/Cart';

export const AppRoutes = () => (
  <Routes>
    <Route path="/" element={<MainLayout />}>
      <Route index element={<Home />} />
      <Route path="login" element={<Login />} />
      <Route path="products" element={<Products />} />
      <Route path="cart" element={<Cart />} />
    </Route>
  </Routes>
);