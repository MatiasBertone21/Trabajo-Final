from fastapi import APIRouter
from app.models.cart import CartResponse, CartItemAdd
from app.services import cart_service

router = APIRouter()

@router.get("/", response_model=CartResponse, summary="Obtener carrito")
def get_cart():
    return cart_service.get_cart()

@router.post("/items", response_model=CartResponse, summary="Agregar producto")
def add_item(item: CartItemAdd):
    return cart_service.add_to_cart(item.productId, item.quantity)

@router.put("/items/{productId}", response_model=CartResponse, summary="Actualizar cantidad")
def update_item(productId: int, quantity: int):
    return cart_service.update_cart_item(productId, quantity)

@router.delete("/items/{productId}", response_model=CartResponse, summary="Eliminar producto")
def delete_item(productId: int):
    return cart_service.remove_from_cart(productId)

@router.delete("/", response_model=CartResponse, summary="Vaciar carrito")
def clear_cart():
    return cart_service.clear_cart()