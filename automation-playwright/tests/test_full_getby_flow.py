import os
from dotenv import load_dotenv
import pytest
from pages.home_page import HomePage
from pages.login_page import LoginPage
from pages.products_page import ProductsPage
from pages.cart_page import CartPage

load_dotenv()


@pytest.mark.getby_full
def test_full_getby_flow_after_login(page, env, base_url, getby_selectors):
    """
    Phase 6 Full Semantic `get_by` E2E Benchmark (`getby_full`):
    1:1 functional counterpart of `test_full_vision_flow_after_login` (`opencv_full`)
    using Playwright's native semantic locators (`get_by_role`, `get_by_test_id`, `filter`):
      1. `login.go_to_products_get_by()`
      2. `products.audit_catalog_and_add_to_cart_get_by(items_to_add=2)` (validates basketball + Laptop Pro cards, Cart=0, and clicks both Add to Cart)
      3. `products.verify_cart_and_open_get_by(expected=2)` (validates Cart=2 and opens `/cart`)
      4. `cart.audit_cart_item_and_remove_get_by("basketball")` (validates thumb, title, description, -, +, remove & clicks remove)
      5. `cart.expect_product_not_in_cart_get_by("basketball")` (verifies basketball is no longer present in `/cart`)
    """
    home = HomePage(page, base_url, getby_selectors, env=env)
    home.goto()
    home.go_to_login_get_by()

    login = LoginPage(page, base_url, getby_selectors, env=env)
    login.fill_login_form_get_by(os.getenv("USER_EMAIL"), os.getenv("USER_PASSWORD"))
    login.submit_get_by()
    page.wait_for_url(f"{base_url}/", timeout=8000)
    login.go_to_products_get_by()

    products = ProductsPage(page, base_url, getby_selectors, env=env)
    products.audit_catalog_and_add_to_cart_get_by(items_to_add=2)
    products.verify_cart_and_open_get_by(expected=2)

    cart = CartPage(page, base_url, getby_selectors, env=env)
    cart.audit_cart_item_and_remove_get_by("basketball")
    cart.expect_product_not_in_cart_get_by("basketball")

