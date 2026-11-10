"""
Script: Harvest Templates (Automated UI Template Harvester)

Purpose:
    Automatically navigate across the Automation Lab frontends (React, Svelte, Angular),
    locate UI elements using the framework's verified selectors, and capture 1:1 subpixel
    crops organized by environment under templates/{env}/.

    Additionally decomposes:
      - A product card (e.g., basketball) into templates/{env}/product-card/
      - A cart item (e.g., basketball) into templates/{env}/cart-item/

Usage:
    python utils/harvest_templates.py --env all
    python utils/harvest_templates.py --env svelte --product basketball
    python utils/harvest_templates.py --env react --product basketball --headed
"""

import os
import sys
import platform
import argparse
from pathlib import Path

# Prevent utils/selectors.py from shadowing Python's stdlib 'selectors' module
# when running 'python utils/harvest_templates.py' directly.
SCRIPT_DIR = str(Path(__file__).resolve().parent)
PLAYWRIGHT_ROOT = Path(__file__).resolve().parent.parent
if SCRIPT_DIR in sys.path:
    sys.path.remove(SCRIPT_DIR)
if str(PLAYWRIGHT_ROOT) not in sys.path:
    sys.path.insert(0, str(PLAYWRIGHT_ROOT))

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, Page, Locator
from utils.selectors import SELECTORS

# Load environment variables
load_dotenv(PLAYWRIGHT_ROOT / ".env")

ENV_URLS = {
    "react": os.getenv("REACT_URL", "http://localhost:3000"),
    "angular": os.getenv("ANGULAR_URL", "http://localhost:4200"),
    "svelte": os.getenv("SVELTE_URL", "http://localhost:5173"),
}

USER_EMAIL = os.getenv("USER_EMAIL", "admin@test.com")
USER_PASSWORD = os.getenv("USER_PASSWORD", "admin123")

# Declarative catalog of global UI elements to capture per page
HARVEST_PLAN = {
    "login": {
        "url": "/login",
        "elements": [
            ("login_email", "login-email-input.png"),
            ("login_password", "login-password-input.png"),
            ("login_submit", "login-submit-btn.png"),
        ],
    },
    "home": {
        "url": "/",
        "requires_auth": True,
        "elements": [
            ("nav_products", "home-nav-products-btn.png"),
            ("nav_cart", "home-nav-cart-btn.png"),
            ("logout", "home-logout-btn.png"),
        ],
    },
    "products": {
        "url": "/products",
        "requires_auth": True,
        "elements": [
            ("add_to_cart", "products-add-to-cart-btn.png"),
        ],
    },
}


def _capture_locator(locator: Locator, output_path: Path, label: str):
    """Wait for the relative locator to become visible and capture a 1:1 screenshot."""
    try:
        locator.wait_for(state="visible", timeout=3000)
        locator.screenshot(path=str(output_path), animations="disabled")
        print(f"    [SUBCOMPONENT OK] {label} -> {output_path.name}")
    except Exception as e:
        print(f"    [SUBCOMPONENT SKIP] Could not capture {label} ({output_path.name}): {e}")


def _capture_element(page: Page, selector: str, output_path: Path, label: str):
    """Wait for the page selector to become visible and capture a 1:1 screenshot."""
    try:
        locator = page.locator(selector).first
        locator.wait_for(state="visible", timeout=4000)
        locator.screenshot(path=str(output_path), animations="disabled")
        print(f"  [CAPTURE OK] {label} -> {output_path.name}")
    except Exception as e:
        print(f"  [SKIPPED] Could not capture '{selector}' ({label}): {e}")


def _harvest_product_card(page: Page, env_name: str, base_output_dir: Path, product_filter: str) -> Locator | None:
    """
    Locate the product card matching product_filter (e.g., 'basketball')
    and atomically capture each of its subcomponents into:
        templates/{env}/product-card/
    Returns the found card locator so it can subsequently be added to the cart.
    """
    card_output_dir = base_output_dir / "product-card"
    card_output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n  [Product Card] Decomposing card for '{product_filter}' in {env_name}...")

    container_selectors = {
        "svelte": "article.product-card",
        "react": "div.product-card",
        "angular": "article.catalog-card, [data-testid^='catalog-item-']",
    }
    card_sel = container_selectors.get(env_name, ".product-card, .catalog-card, article")

    # Locate all cards and filter by product name/text (case-insensitive)
    cards = page.locator(card_sel)
    target_card = cards.filter(has_text=product_filter).first

    try:
        target_card.wait_for(state="visible", timeout=5000)
    except Exception as e:
        print(f"  [WARN] Could not find visible card with text '{product_filter}' in {env_name}: {e}")
        return None

    # 1. Full product card container
    _capture_locator(target_card, card_output_dir / "product-card-container.png", f"{env_name}: Full Card")

    # 2. Inner subcomponents (relative to target_card)
    subcomponents = [
        ("img", "product-card-image.png", "Image"),
        ("h2, h3, .product-title", "product-card-title.png", "Title"),
        (".category, p.category, span.category, p:not(:has-text('Stock'))", "product-card-category.png", "Category"),
        ("strong, .price, .product-price", "product-card-price.png", "Price"),
        (".detail-link, a:has-text('View details'), a:has-text('Detalles')", "product-card-view-details-btn.png", "Details Button"),
        ("button, .add, .button-primary, [role='button'].add", "product-card-add-to-bag-btn.png", "Add Button"),
    ]

    # Environment-specific description subcomponent (e.g., Svelte)
    if env_name == "svelte":
        subcomponents.append((".product-body p:not(.category)", "product-card-description.png", "Description"))

    for sub_sel, filename, label in subcomponents:
        loc = target_card.locator(sub_sel).first
        _capture_locator(loc, card_output_dir / filename, f"{env_name}: {label}")

    # 3. Also capture the full 'Laptop Pro' card container for hierarchical spatial resolution (parent-child BBox)
    laptop_card = cards.filter(has_text="Laptop").first
    try:
        laptop_card.wait_for(state="visible", timeout=3000)
        _capture_locator(
            laptop_card,
            card_output_dir / "laptop-card-container.png",
            f"{env_name}: Full Card (Laptop Pro)",
        )
    except Exception as e:
        print(f"  [WARN] Could not capture 'laptop-card-container.png' in {env_name}: {e}")

    return target_card


def _harvest_cart_item(page: Page, env_name: str, base_output_dir: Path, product_filter: str):
    """
    Locate the cart row for the specified product (e.g., 'basketball')
    and capture its subcomponents into:
        templates/{env}/cart-item/
    """
    cart_item_dir = base_output_dir / "cart-item"
    cart_item_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n  [Cart Item] Decomposing cart row for '{product_filter}' in {env_name}...")

    row_selectors = {
        "react": "[data-testid='cart-item']",
        "angular": ".cart-row",
        "svelte": "article.cart-item",
    }
    row_sel = row_selectors.get(env_name, "[data-testid='cart-item'], .cart-row, article.cart-item")

    rows = page.locator(row_sel)
    target_row = rows.filter(has_text=product_filter).first

    try:
        target_row.wait_for(state="visible", timeout=5000)
    except Exception as e:
        print(f"  [WARN] Could not find cart row with text '{product_filter}' in {env_name}: {e}")
        return

    # 1. Full cart row container
    _capture_locator(target_row, cart_item_dir / "cart-item-container.png", f"{env_name}: Full Cart Item")

    # 2. Inner subcomponents per environment
    env_subcomponents = {
        "react": [
            ("img", "cart-item-image.png", "Thumbnail Image"),
            ("[data-testid='cart-item-name']", "cart-item-title.png", "Product Title"),
            ("[data-testid='cart-item-description']", "cart-item-description.png", "Product Description"),
            ("[data-testid='decrease-quantity']", "cart-item-decrease-btn.png", "Decrease Button (-)"),
            ("[data-testid='increase-quantity']", "cart-item-increase-btn.png", "Increase Button (+)"),
            ("[data-testid='remove-item-button']", "cart-item-remove-btn.png", "Remove Button"),
        ],
        "angular": [
            ("img.cart-thumb, img", "cart-item-image.png", "Thumbnail Image"),
            (".cart-label", "cart-item-title.png", "Product Title"),
            (".item-details .cart-meta:first-of-type", "cart-item-description.png", "Product Description"),
            ("[data-testid^='cart-decrease-']", "cart-item-decrease-btn.png", "Decrease Button (-)"),
            ("[data-testid^='cart-increase-']", "cart-item-increase-btn.png", "Increase Button (+)"),
            ("button.remove, [data-testid^='cart-remove-']", "cart-item-remove-btn.png", "Remove Button"),
        ],
        "svelte": [
            ("img", "cart-item-image.png", "Thumbnail Image"),
            (".item-details h2", "cart-item-title.png", "Product Title"),
            (".item-controls button:first-of-type", "cart-item-decrease-btn.png", "Decrease Button (-)"),
            (".item-controls button:last-of-type", "cart-item-increase-btn.png", "Increase Button (+)"),
            ("button.remove-button", "cart-item-remove-btn.png", "Remove Button"),
        ],
    }

    for sub_sel, filename, label in env_subcomponents.get(env_name, []):
        loc = target_row.locator(sub_sel).first
        _capture_locator(loc, cart_item_dir / filename, f"{env_name}: {label}")

    # Clean up the item from the cart after capturing templates
    try:
        remove_selectors = {
            "react": "[data-testid='remove-item-button']",
            "angular": "button.remove, [data-testid^='cart-remove-']",
            "svelte": "button.remove-button",
        }
        rem_btn = target_row.locator(remove_selectors[env_name]).first
        if rem_btn.is_visible():
            rem_btn.click()
            page.wait_for_timeout(400)
            print(f"    [CLEANUP] Item '{product_filter}' removed from cart in {env_name}.")
    except Exception:
        pass


def harvest_for_env(page: Page, env_name: str, base_url: str, product_filter: str = "basketball"):
    """Execute template harvesting for a specific frontend environment."""
    print(f"\n{'='*60}")
    print(f" Starting template harvesting for: {env_name.upper()} ({base_url})")
    print(f"{'='*60}")

    env_selectors = SELECTORS.get(env_name)
    if not env_selectors:
        print(f"[ERROR] No selectors configured for '{env_name}'.")
        return

    output_dir = PLAYWRIGHT_ROOT / "templates" / env_name
    output_dir.mkdir(parents=True, exist_ok=True)

    logged_in = False

    # 1. Login Phase
    login_config = HARVEST_PLAN["login"]
    login_url = f"{base_url}{login_config['url']}"
    print(f"\n[1/4] Navigating to Login: {login_url}")
    try:
        page.goto(login_url, wait_until="domcontentloaded", timeout=15000)
        page.wait_for_timeout(1000)

        for selector_key, filename in login_config["elements"]:
            selector = env_selectors.get(selector_key)
            if not selector:
                continue
            _capture_element(page, selector, output_dir / filename, f"{env_name}: {filename}")

        # Perform login to unlock Home and Products
        email_sel = env_selectors.get("login_email")
        pass_sel = env_selectors.get("login_password")
        submit_sel = env_selectors.get("login_submit")

        if email_sel and pass_sel and submit_sel:
            page.fill(email_sel, USER_EMAIL)
            page.fill(pass_sel, USER_PASSWORD)
            page.click(submit_sel)
            page.wait_for_url(f"{base_url}/", timeout=8000)
            logged_in = True
            print("  [OK] Login authenticated successfully.")
    except Exception as e:
        print(f"  [WARN] Login flow failed in {env_name}: {e}")

    # 2. Home Phase
    if logged_in:
        home_config = HARVEST_PLAN["home"]
        print(f"\n[2/4] Processing Home Page: {base_url}/")
        try:
            page.goto(f"{base_url}/", wait_until="domcontentloaded", timeout=10000)
            page.wait_for_timeout(1000)

            for selector_key, filename in home_config["elements"]:
                selector = env_selectors.get(selector_key)
                if not selector:
                    continue
                _capture_element(page, selector, output_dir / filename, f"{env_name}: {filename}")
        except Exception as e:
            print(f"  [WARN] Error processing Home in {env_name}: {e}")

    # 3. Products & Product Card Phase
    products_config = HARVEST_PLAN["products"]
    products_url = f"{base_url}{products_config['url']}"
    print(f"\n[3/4] Navigating to Products: {products_url}")
    try:
        page.goto(products_url, wait_until="domcontentloaded", timeout=10000)
        page.wait_for_timeout(1000)

        for selector_key, filename in products_config["elements"]:
            selector = env_selectors.get(selector_key)
            if not selector:
                continue
            _capture_element(page, selector, output_dir / filename, f"{env_name}: {filename}")

        # Harvest templates for the selected product card (e.g., basketball)
        target_card = _harvest_product_card(page, env_name, output_dir, product_filter)

        # 4. Cart & Cart Item Phase (add product to cart and navigate to /cart)
        if target_card is not None:
            print(f"\n[4/4] Adding '{product_filter}' to cart and navigating to /cart in {env_name}...")
            add_btn = target_card.locator("button, .add, .button-primary, [role='button'].add").first
            add_btn.click()
            page.wait_for_timeout(600)

            nav_cart_sel = env_selectors.get("nav_cart")
            if nav_cart_sel:
                page.locator(nav_cart_sel).first.click()
            else:
                page.goto(f"{base_url}/cart", wait_until="domcontentloaded", timeout=10000)
            page.wait_for_timeout(1000)

            _harvest_cart_item(page, env_name, output_dir, product_filter)

    except Exception as e:
        print(f"  [WARN] Error processing Products/Cart in {env_name}: {e}")

    print(f"\n [DONE] Templates for {env_name.upper()} saved to: {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="Harvest UI templates from Automation Lab frontends.")
    parser.add_argument(
        "--env",
        choices=["react", "angular", "svelte", "all"],
        default="all",
        help="Frontend environment to harvest templates from (default: all)"
    )
    parser.add_argument(
        "--product", "-p",
        default="basketball",
        help="Product name/substring to filter the card for template decomposition (default: basketball)"
    )
    parser.add_argument(
        "--headed",
        action="store_true",
        help="Run browser in visible mode (default: headless)"
    )

    args = parser.parse_args()

    target_envs = ["react", "angular", "svelte"] if args.env == "all" else [args.env]

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=not args.headed,
            slow_mo=250 if args.headed else 0,
        )
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        page = context.new_page()

        for env_name in target_envs:
            base_url = ENV_URLS.get(env_name)
            if not base_url:
                print(f"[SKIP] URL not defined for environment '{env_name}'")
                continue
            harvest_for_env(page, env_name, base_url, product_filter=args.product)

        context.close()
        browser.close()

    # Record the OS platform on which the templates were rendered
    os_marker = PLAYWRIGHT_ROOT / "templates" / ".harvested_os"
    os_marker.parent.mkdir(parents=True, exist_ok=True)
    os_marker.write_text(platform.system(), encoding="utf-8")


if __name__ == "__main__":
    main()
