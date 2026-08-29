from fastapi import APIRouter, Request
from app.models.cart import CartResponse, CartItemAdd
from app.services import cart_service

router = APIRouter()

@router.get("/", response_model=CartResponse, summary="Obtener carrito")
def get_cart(request: Request):
    return cart_service.get_cart(request.headers.get("X-Cart-Scope"))

@router.post("/items", response_model=CartResponse, summary="Agregar producto")
def add_item(item: CartItemAdd, request: Request):
    return cart_service.add_to_cart(item.productId, item.quantity, request.headers.get("X-Cart-Scope"))

@router.put("/items/{productId}", response_model=CartResponse, summary="Actualizar cantidad")
def update_item(productId: int, quantity: int, request: Request):
    return cart_service.update_cart_item(productId, quantity, request.headers.get("X-Cart-Scope"))

@router.delete("/items/{productId}", response_model=CartResponse, summary="Eliminar producto")
def delete_item(productId: int, request: Request):
    return cart_service.remove_from_cart(productId, request.headers.get("X-Cart-Scope"))

@router.delete("/", response_model=CartResponse, summary="Vaciar carrito")
def clear_cart(request: Request):
    return cart_service.clear_cart(request.headers.get("X-Cart-Scope"))