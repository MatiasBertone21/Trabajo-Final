import os
from dotenv import load_dotenv
import pytest
from pages.home_page import HomePage
from pages.login_page import LoginPage
from pages.products_page import ProductsPage
from pages.cart_page import CartPage

load_dotenv()

@pytest.mark.base
def test_add_to_cart_with_base_strategy_reflects_in_cart(page,base_url, base_selectors):
    home = HomePage(page, base_url, base_selectors)
    home.goto()
    login = LoginPage(page, base_url, base_selectors)
    login.go_to_login()
    login.fill_credentials(os.getenv("USER_EMAIL"), os.getenv("USER_PASSWORD"))
    login.submit()
    page.wait_for_url(f"{base_url}/", timeout=8000)
    login.is_redirected_to_home()

    products = ProductsPage(page, base_url, base_selectors)
    products.goto()
    products.page.pause()
    products.add_to_cart(index=0)

    products.go_to_cart()
    cart = CartPage(page,base_url, base_selectors)
    cart.expect_cart_count(expected=1)
    cart.remove_item(index=0)
    cart.expect_cart_count(expected=0)
    cart.logout()

@pytest.mark.getby
def test_add_to_cart_with_getby_strategy_reflects_in_cart(page,base_url, getby_selectors):
    home = HomePage(page, base_url, getby_selectors)
    home.goto()
    home.go_to_login_get_by()

    login = LoginPage(page, base_url, getby_selectors)
    login.fill_login_form_get_by(os.getenv("USER_EMAIL"), os.getenv("USER_PASSWORD"))
    login.submit_get_by()
    login.go_to_products_get_by()

    products = ProductsPage(page,base_url, getby_selectors)
    products.add_to_cart_get_by(index=0)
    products.go_to_cart_get_by()

    cart = CartPage(page, base_url, getby_selectors)
    cart.expect_cart_count_get_by(expected=1)
    cart.remove_item_get_by()
    cart.expect_cart_count_get_by(expected=0)
    cart.logout_get_by()
