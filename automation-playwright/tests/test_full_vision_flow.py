import os
from dotenv import load_dotenv
import pytest
from pages.home_page import HomePage
from pages.login_page import LoginPage
from pages.products_page import ProductsPage
from pages.cart_page import CartPage

load_dotenv()


@pytest.mark.opencv_full
def test_full_vision_flow_after_login(page, env, base_url, getby_selectors):
    """
    Phase 6 Full-Vision E2E Benchmark (`opencv_full`) following strict POM architecture:
    - Precondition (Login): Semantic `get_by` locators via `HomePage` and `LoginPage`.
    - Post-Login E2E Flow: 100% driven and validated via `vision-service` (OpenCV + Adaptive EasyOCR):
      1. `login.go_to_products_opencv()` (`enable_ocr=False`)
      2. `products.audit_catalog_and_add_to_cart_opencv(items_to_add=2)` (`enable_ocr=False` structure + `enable_ocr=True` Cart=0 + 2 items)
      3. `products.verify_cart_and_open_opencv(expected=2)` (`enable_ocr=True` soft-assert + click Cart)
      4. `cart.audit_cart_item_and_remove_opencv("basketball")` (validates thumb, title, description, -, +, remove & clicks remove)
      5. `cart.expect_product_not_in_cart_opencv("basketball")` (verifies basketball is no longer present in `/cart`)
    """
    home = HomePage(page, base_url, getby_selectors, env=env)
    home.goto()
    home.go_to_login_get_by()

    login = LoginPage(page, base_url, getby_selectors, env=env)
    login.fill_login_form_get_by(os.getenv("USER_EMAIL"), os.getenv("USER_PASSWORD"))
    login.submit_get_by()
    page.wait_for_url(f"{base_url}/", timeout=8000)
    login.go_to_products_opencv()

    products = ProductsPage(page, base_url, env=env)
    products.audit_catalog_and_add_to_cart_opencv(items_to_add=2)
    products.verify_cart_and_open_opencv(expected=2)

    cart = CartPage(page, base_url, env=env)
    cart.audit_cart_item_and_remove_opencv("basketball")
    cart.expect_product_not_in_cart_opencv("basketball")
