from fastapi import HTTPException
from app.repositories.json_repo import JSONRepository

order_repo = JSONRepository("orders.json")

def get_all_orders():
    return order_repo.read_all()

def get_order_by_id(order_id: int):
    orders = order_repo.read_all()
    order = next((o for o in orders if o["id"] == order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    return order