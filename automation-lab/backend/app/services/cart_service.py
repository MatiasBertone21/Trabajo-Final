import logging
from fastapi import HTTPException
from app.repositories.json_repo import JSONRepository
from app.models.cart import CartResponse

logger = logging.getLogger(__name__)
cart_repo = JSONRepository("cart.json")
product_repo = JSONRepository("products.json")

def get_cart() -> dict:
    items = cart_repo.read_all()
    total_items = sum(item["quantity"] for item in items)
    total_amount = sum(item["subtotal"] for item in items)
    return {"items": items, "totalItems": total_items, "totalAmount": total_amount}

def add_to_cart(product_id: int, quantity: int):
    if quantity <= 0:
        raise HTTPException(status_code=400, detail="La cantidad debe ser mayor a cero")

    products = product_repo.read_all()
    product = next((p for p in products if p["id"] == product_id), None)
    
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    cart = cart_repo.read_all()
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

    cart_repo.write_all(cart)
    logger.info(f"Producto {product_id} agregado al carrito.")
    return get_cart()

def update_cart_item(product_id: int, quantity: int):
    if quantity <= 0:
        raise HTTPException(status_code=400, detail="La cantidad debe ser mayor a cero")
        
    cart = cart_repo.read_all()
    item = next((i for i in cart if i["productId"] == product_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Producto no está en el carrito")
        
    products = product_repo.read_all()
    product = next((p for p in products if p["id"] == product_id), None)
    
    if quantity > product["stock"]:
        raise HTTPException(status_code=409, detail="La cantidad supera el stock disponible")

    item["quantity"] = quantity
    item["subtotal"] = quantity * item["unitPrice"]
    
    cart_repo.write_all(cart)
    return get_cart()

def remove_from_cart(product_id: int):
    cart = cart_repo.read_all()
    new_cart = [item for item in cart if item["productId"] != product_id]
    
    if len(cart) == len(new_cart):
        raise HTTPException(status_code=404, detail="Producto no encontrado en el carrito")
        
    cart_repo.write_all(new_cart)
    logger.info(f"Producto {product_id} eliminado del carrito.")
    return get_cart()

def clear_cart():
    cart_repo.write_all([])
    return get_cart()