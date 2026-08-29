import logging
from fastapi import HTTPException
from app.repositories.json_repo import JSONRepository
from app.models.cart import CartResponse

logger = logging.getLogger(__name__)
cart_repo = JSONRepository("cart.json")
product_repo = JSONRepository("products.json")

def _normalize_scope(scope: str | None) -> str:
    if not scope:
        return "default"

    cleaned = "".join(ch for ch in scope.strip().lower() if ch.isalnum() or ch in {"-", "_"})
    return cleaned[:40] if cleaned else "default"


def _read_scoped_carts() -> dict[str, list[dict]]:
    raw = cart_repo.read_all()

    # Legacy format used a single list for every client.
    if isinstance(raw, list):
        return {"default": raw}

    # New format is a dict where each key represents one cart scope.
    if isinstance(raw, dict):
        scoped: dict[str, list[dict]] = {}
        for key, value in raw.items():
            if isinstance(value, list):
                scoped[_normalize_scope(str(key))] = value
        return scoped

    return {"default": []}


def _write_scoped_carts(scoped_carts: dict[str, list[dict]]) -> None:
    cart_repo.write_all(scoped_carts)


def _get_scope_items(scoped_carts: dict[str, list[dict]], scope: str) -> list[dict]:
    return list(scoped_carts.get(scope, []))


def get_cart(scope: str | None = None) -> dict:
    scope_key = _normalize_scope(scope)
    scoped_carts = _read_scoped_carts()
    items = _get_scope_items(scoped_carts, scope_key)
    total_items = sum(item["quantity"] for item in items)
    total_amount = sum(item["subtotal"] for item in items)
    return {"items": items, "totalItems": total_items, "totalAmount": total_amount}

def add_to_cart(product_id: int, quantity: int, scope: str | None = None):
    if quantity <= 0:
        raise HTTPException(status_code=400, detail="La cantidad debe ser mayor a cero")

    scope_key = _normalize_scope(scope)

    products = product_repo.read_all()
    product = next((p for p in products if p["id"] == product_id), None)
    
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    scoped_carts = _read_scoped_carts()
    cart = _get_scope_items(scoped_carts, scope_key)
    existing_item = next((item for item in cart if item["productId"] == product_id), None)
    
    current_qty = existing_item["quantity"] if existing_item else 0
    if current_qty + quantity > product["stock"]:
        raise HTTPException(status_code=409, detail="La cantidad supera el stock disponible")

    if existing_item:
        existing_item["quantity"] += quantity
        existing_item["subtotal"] = existing_item["quantity"] * existing_item["unitPrice"]
    else:
        cart.append({
            "productId": product["id"],
            "productName": product["name"],
            "quantity": quantity,
            "unitPrice": product["price"],
            "subtotal": product["price"] * quantity
        })

    scoped_carts[scope_key] = cart
    _write_scoped_carts(scoped_carts)
    logger.info(f"Producto {product_id} agregado al carrito.")
    return get_cart(scope_key)

def update_cart_item(product_id: int, quantity: int, scope: str | None = None):
    if quantity <= 0:
        raise HTTPException(status_code=400, detail="La cantidad debe ser mayor a cero")

    scope_key = _normalize_scope(scope)
        
    scoped_carts = _read_scoped_carts()
    cart = _get_scope_items(scoped_carts, scope_key)
    item = next((i for i in cart if i["productId"] == product_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Producto no está en el carrito")
        
    products = product_repo.read_all()
    product = next((p for p in products if p["id"] == product_id), None)
    
    if quantity > product["stock"]:
        raise HTTPException(status_code=409, detail="La cantidad supera el stock disponible")

    item["quantity"] = quantity
    item["subtotal"] = quantity * item["unitPrice"]
    
    scoped_carts[scope_key] = cart
    _write_scoped_carts(scoped_carts)
    return get_cart(scope_key)

def remove_from_cart(product_id: int, scope: str | None = None):
    scope_key = _normalize_scope(scope)
    scoped_carts = _read_scoped_carts()
    cart = _get_scope_items(scoped_carts, scope_key)
    new_cart = [item for item in cart if item["productId"] != product_id]
    
    if len(cart) == len(new_cart):
        raise HTTPException(status_code=404, detail="Producto no encontrado en el carrito")

    scoped_carts[scope_key] = new_cart
    _write_scoped_carts(scoped_carts)
    logger.info(f"Producto {product_id} eliminado del carrito.")
    return get_cart(scope_key)

def clear_cart(scope: str | None = None):
    scope_key = _normalize_scope(scope)
    scoped_carts = _read_scoped_carts()
    scoped_carts[scope_key] = []
    _write_scoped_carts(scoped_carts)
    return get_cart(scope_key)