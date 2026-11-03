from pydantic import BaseModel
from typing import List

class CartItemAdd(BaseModel):
    productId: int
    quantity: int

class CartItem(BaseModel):
    productId: int
    productName: str
    description: str | None = None
    image: str | None = None
    quantity: int
    unitPrice: float
    subtotal: float

class CartResponse(BaseModel):
    items: List[CartItem]
    totalItems: int
    totalAmount: float
