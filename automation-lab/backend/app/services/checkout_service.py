import logging
from datetime import datetime
from fastapi import HTTPException
from app.repositories.json_repo import JSONRepository
from app.services import cart_service

logger = logging.getLogger(__name__)
product_repo = JSONRepository("products.json")
order_repo = JSONRepository("orders.json")

def process_checkout():
    logger.info("Checkout iniciado.")
    cart_data = cart_service.get_cart()
    items = cart_data["items"]
    
    if not items:
        logger.warning("Checkout fallido: Carrito vacío.")
        raise HTTPException(status_code=400, detail="El carrito está vacío")

    products = product_repo.read_all()
    
    # 1. Validar stock de todos los items antes de modificar nada
    for item in items:
        product = next((p for p in products if p["id"] == item["productId"]), None)
        if not product or item["quantity"] > product["stock"]:
            logger.warning(f"Checkout fallido: Stock insuficiente para {item['productName']}.")
            raise HTTPException(status_code=409, detail=f"Stock insuficiente para {item['productName']}")

    # 2. Descontar stock
    for item in items:
        product = next(p for p in products if p["id"] == item["productId"])
        product["stock"] -= item["quantity"]
    
    product_repo.write_all(products)

    # 3. Generar Orden
    orders = order_repo.read_all()
    new_id = max([o["id"] for o in orders], default=0) + 1
    
    new_order = {
        "id": new_id,
        "createdAt": datetime.now().isoformat(),
        "user": "user@test.com", # Hardcodeado por la naturaleza Fake de la API
        "products": items,
        "total": cart_data["totalAmount"],
        "status": "CREATED"
    }
    
    orders.append(new_order)
    order_repo.write_all(orders)

    # 4. Vaciar carrito
    cart_service.clear_cart()
    
    logger.info(f"Checkout exitoso. Orden creada: {new_id}.")
    return new_order