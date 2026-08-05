import { Routes } from '@angular/router';
import { MainLayout } from './layouts/main-layout';
import { HomePage } from './pages/home/home-page';
import { ProductsPage } from './pages/products/products-page';
import { ProductDetailPage } from './pages/product-detail/product-detail-page';
import { CartPage } from './pages/cart/cart-page';
import { LoginPage } from './pages/login/login-page';
import { authGuard } from './guards/auth.guard';

export const routes: Routes = [
	{ path: 'login', component: LoginPage },
	{
		path: '',
		component: MainLayout,
		children: [
			{ path: '', component: HomePage },
			{ path: 'products', component: ProductsPage },
			{ path: 'products/:id', component: ProductDetailPage },
			{ path: 'cart', component: CartPage, canActivate: [authGuard] },
		],
	},
];
