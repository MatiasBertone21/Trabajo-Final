"""
Script: Harvest Templates (Generador Automatizado de Plantillas UI)

Propósito:
    Navegar automáticamente a través de los entornos de Automation Lab (React, Svelte, Angular),
    localizar los elementos de interfaz usando los selectores probados del framework,
    y capturar recortes de subpíxel 1:1 guardándolos organizados por entorno en templates/{env}/.

    Además, permite descomponer:
      - Una tarjeta de producto (e.g. basketball) en templates/{env}/product-card/
      - Un ítem del carrito (e.g. basketball) en templates/{env}/cart-item/

Uso:
    python utils/harvest_templates.py --env all
    python utils/harvest_templates.py --env svelte --product basketball
    python utils/harvest_templates.py --env react --product basketball --headed
"""

import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, Page, Locator

# Agregar la raíz de automation-playwright al path de importación
PLAYWRIGHT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLAYWRIGHT_ROOT))

from utils.selectors import SELECTORS

# Cargar variables de entorno
load_dotenv(PLAYWRIGHT_ROOT / ".env")

ENV_URLS = {
    "react": os.getenv("REACT_URL", "http://localhost:3000"),
    "angular": os.getenv("ANGULAR_URL", "http://localhost:4200"),
    "svelte": os.getenv("SVELTE_URL", "http://localhost:5173"),
}

USER_EMAIL = os.getenv("USER_EMAIL", "admin@test.com")
USER_PASSWORD = os.getenv("USER_PASSWORD", "admin123")

# Catálogo declarativo de elementos globales a capturar por página
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
    """Espera que el locator relativo sea visible y toma su captura 1:1."""
    try:
        locator.wait_for(state="visible", timeout=3000)
        locator.screenshot(path=str(output_path), animations="disabled")
        print(f"    [SUBCOMPONENT OK] {label} -> {output_path.name}")
    except Exception as e:
        print(f"    [SUBCOMPONENT SKIP] No se pudo capturar {label} ({output_path.name}): {e}")


def _capture_element(page: Page, selector: str, output_path: Path, label: str):
    """Espera que el selector en página sea visible y toma su captura 1:1."""
    try:
        locator = page.locator(selector).first
        locator.wait_for(state="visible", timeout=4000)
        locator.screenshot(path=str(output_path), animations="disabled")
        print(f"  [CAPTURA OK] {label} -> {output_path.name}")
    except Exception as e:
        print(f"  [OMITIDO] No se pudo capturar '{selector}' ({label}): {e}")


def _harvest_product_card(page: Page, env_name: str, base_output_dir: Path, product_filter: str) -> Locator | None:
    """
    Localiza la tarjeta del producto especificado por product_filter (ej: 'basketball')
    y captura atómicamente cada uno de sus subcomponentes dentro de:
        templates/{env}/product-card/
    Devuelve el locator de la tarjeta encontrada para poder agregarla al carrito.
    """
    card_output_dir = base_output_dir / "product-card"
    card_output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n  [Product Card] Descomponiendo tarjeta de '{product_filter}' en {env_name}...")

    container_selectors = {
        "svelte": "article.product-card",
        "react": "div.product-card",
        "angular": "article.catalog-card, [data-testid^='catalog-item-']",
    }
    card_sel = container_selectors.get(env_name, ".product-card, .catalog-card, article")

    # Localizar todas las tarjetas y filtrar por el nombre/texto del producto (insensible a mayúsculas)
    cards = page.locator(card_sel)
    target_card = cards.filter(has_text=product_filter).first

    try:
        target_card.wait_for(state="visible", timeout=5000)
    except Exception as e:
        print(f"  [WARN] No se encontró tarjeta visible con texto '{product_filter}' en {env_name}: {e}")
        return None

    # 1. Contenedor completo de la tarjeta
    _capture_locator(target_card, card_output_dir / "product-card-container.png", f"{env_name}: Tarjeta Completa")

    # 2. Subcomponentes internos (relativos a target_card)
    subcomponents = [
        ("img", "product-card-image.png", "Imagen"),
        ("h2, h3, .product-title", "product-card-title.png", "Título"),
        (".category, p.category, span.category, p:not(:has-text('Stock'))", "product-card-category.png", "Categoría"),
        ("strong, .price, .product-price", "product-card-price.png", "Precio"),
        (".detail-link, a:has-text('View details'), a:has-text('Detalles')", "product-card-view-details-btn.png", "Botón Detalles"),
        ("button, .add, .button-primary, [role='button'].add", "product-card-add-to-bag-btn.png", "Botón Agregar"),
    ]

    # Subcomponente específico de descripción (e.g. Svelte)
    if env_name == "svelte":
        subcomponents.append((".product-body p:not(.category)", "product-card-description.png", "Descripción"))

    for sub_sel, filename, label in subcomponents:
        loc = target_card.locator(sub_sel).first
        _capture_locator(loc, card_output_dir / filename, f"{env_name}: {label}")

    # 3. Capturar también el contenedor completo de 'Laptop Pro' para resolución espacial jerárquica (BBox padre-hijo)
    laptop_card = cards.filter(has_text="Laptop").first
    try:
        laptop_card.wait_for(state="visible", timeout=3000)
        _capture_locator(
            laptop_card,
            card_output_dir / "laptop-card-container.png",
            f"{env_name}: Tarjeta Completa (Laptop Pro)",
        )
    except Exception as e:
        print(f"  [WARN] No se pudo capturar 'laptop-card-container.png' en {env_name}: {e}")

    return target_card


def _harvest_cart_item(page: Page, env_name: str, base_output_dir: Path, product_filter: str):
    """
    Localiza la fila del carrito para el producto especificado (ej: 'basketball')
    y captura sus subcomponentes dentro de:
        templates/{env}/cart-item/
    """
    cart_item_dir = base_output_dir / "cart-item"
    cart_item_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n  [Cart Item] Descomponiendo fila de carrito de '{product_filter}' en {env_name}...")

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
        print(f"  [WARN] No se encontró fila de carrito con texto '{product_filter}' en {env_name}: {e}")
        return

    # 1. Contenedor completo de la fila del carrito
    _capture_locator(target_row, cart_item_dir / "cart-item-container.png", f"{env_name}: Cart Item Completo")

    # 2. Subcomponentes internos por entorno
    env_subcomponents = {
        "react": [
            ("img", "cart-item-image.png", "Imagen Miniatura"),
            ("[data-testid='cart-item-name']", "cart-item-title.png", "Título Producto"),
            ("[data-testid='cart-item-description']", "cart-item-description.png", "Descripción Producto"),
            ("[data-testid='decrease-quantity']", "cart-item-decrease-btn.png", "Botón Menos (-)"),
            ("[data-testid='increase-quantity']", "cart-item-increase-btn.png", "Botón Más (+)"),
            ("[data-testid='remove-item-button']", "cart-item-remove-btn.png", "Botón Eliminar"),
        ],
        "angular": [
            ("img.cart-thumb, img", "cart-item-image.png", "Imagen Miniatura"),
            (".cart-label", "cart-item-title.png", "Título Producto"),
            (".item-details .cart-meta:first-of-type", "cart-item-description.png", "Descripción Producto"),
            ("[data-testid^='cart-decrease-']", "cart-item-decrease-btn.png", "Botón Menos (-)"),
            ("[data-testid^='cart-increase-']", "cart-item-increase-btn.png", "Botón Más (+)"),
            ("button.remove, [data-testid^='cart-remove-']", "cart-item-remove-btn.png", "Botón Quitar"),
        ],
        "svelte": [
            ("img", "cart-item-image.png", "Imagen Miniatura"),
            (".item-details h2", "cart-item-title.png", "Título Producto"),
            (".item-controls button:first-of-type", "cart-item-decrease-btn.png", "Botón Menos (-)"),
            (".item-controls button:last-of-type", "cart-item-increase-btn.png", "Botón Más (+)"),
            ("button.remove-button", "cart-item-remove-btn.png", "Botón Remove"),
        ],
    }

    for sub_sel, filename, label in env_subcomponents.get(env_name, []):
        loc = target_row.locator(sub_sel).first
        _capture_locator(loc, cart_item_dir / filename, f"{env_name}: {label}")

    # Limpiar el producto del carrito tras capturar los templates
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
            print(f"    [CLEANUP] Ítem '{product_filter}' eliminado del carrito en {env_name}.")
    except Exception:
        pass


def harvest_for_env(page: Page, env_name: str, base_url: str, product_filter: str = "basketball"):
    """Ejecuta la captura de templates para un entorno específico."""
    print(f"\n{'='*60}")
    print(f" Iniciando recolección de templates para: {env_name.upper()} ({base_url})")
    print(f"{'='*60}")

    env_selectors = SELECTORS.get(env_name)
    if not env_selectors:
        print(f"[ERROR] No se encontraron selectores configurados para '{env_name}'.")
        return

    output_dir = PLAYWRIGHT_ROOT / "templates" / env_name
    output_dir.mkdir(parents=True, exist_ok=True)

    logged_in = False

    # 1. Fase Login
    login_config = HARVEST_PLAN["login"]
    login_url = f"{base_url}{login_config['url']}"
    print(f"\n[1/4] Navegando a Login: {login_url}")
    try:
        page.goto(login_url, wait_until="domcontentloaded", timeout=15000)
        page.wait_for_timeout(1000)

        for selector_key, filename in login_config["elements"]:
            selector = env_selectors.get(selector_key)
            if not selector:
                continue
            _capture_element(page, selector, output_dir / filename, f"{env_name}: {filename}")

        # Realizar login para desbloquear Home y Products
        email_sel = env_selectors.get("login_email")
        pass_sel = env_selectors.get("login_password")
        submit_sel = env_selectors.get("login_submit")

        if email_sel and pass_sel and submit_sel:
            page.fill(email_sel, USER_EMAIL)
            page.fill(pass_sel, USER_PASSWORD)
            page.click(submit_sel)
            page.wait_for_url(f"{base_url}/", timeout=8000)
            logged_in = True
            print("  [OK] Login autenticado correctamente.")
    except Exception as e:
        print(f"  [WARN] Falló el flujo de login en {env_name}: {e}")

    # 2. Fase Home
    if logged_in:
        home_config = HARVEST_PLAN["home"]
        print(f"\n[2/4] Procesando Home Page: {base_url}/")
        try:
            page.goto(f"{base_url}/", wait_until="domcontentloaded", timeout=10000)
            page.wait_for_timeout(1000)

            for selector_key, filename in home_config["elements"]:
                selector = env_selectors.get(selector_key)
                if not selector:
                    continue
                _capture_element(page, selector, output_dir / filename, f"{env_name}: {filename}")
        except Exception as e:
            print(f"  [WARN] Error procesando Home en {env_name}: {e}")

    # 3. Fase Products & Product Card
    products_config = HARVEST_PLAN["products"]
    products_url = f"{base_url}{products_config['url']}"
    print(f"\n[3/4] Navegando a Products: {products_url}")
    try:
        page.goto(products_url, wait_until="domcontentloaded", timeout=10000)
        page.wait_for_timeout(1000)

        for selector_key, filename in products_config["elements"]:
            selector = env_selectors.get(selector_key)
            if not selector:
                continue
            _capture_element(page, selector, output_dir / filename, f"{env_name}: {filename}")

        # Recolectar templates de la tarjeta seleccionada (e.g. basketball)
        target_card = _harvest_product_card(page, env_name, output_dir, product_filter)

        # 4. Fase Cart & Cart Item (agregar el producto y navegar a /cart)
        if target_card is not None:
            print(f"\n[4/4] Agregando '{product_filter}' al carrito y navegando a /cart en {env_name}...")
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
        print(f"  [WARN] Error procesando Products/Cart en {env_name}: {e}")

    print(f"\n [COMPLETO] Templates de {env_name.upper()} guardados en: {output_dir}")


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
        browser = p.chromium.launch(headless=not args.headed)
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        page = context.new_page()

        for env_name in target_envs:
            base_url = ENV_URLS.get(env_name)
            if not base_url:
                print(f"[SKIP] URL no definida para entorno '{env_name}'")
                continue
            harvest_for_env(page, env_name, base_url, product_filter=args.product)

        context.close()
        browser.close()


if __name__ == "__main__":
    main()
