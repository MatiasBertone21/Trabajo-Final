from fastapi import APIRouter
from app.models.order import Order
from app.services import checkout_service, order_service

router = APIRouter()

@router.post("/checkout", response_model=Order, summary="Procesar checkout")
def process_checkout():
    return checkout_service.process_checkout()

@router.get("/", summary="Listar órdenes")
def list_orders():
    return order_service.get_all_orders()

@router.get("/{orderId}", response_model=Order, summary="Obtener orden por ID")
def get_order(orderId: int):
    return order_service.get_order_by_id(orderId)