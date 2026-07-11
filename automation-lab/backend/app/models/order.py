from pydantic import BaseModel
from typing import List
from enum import Enum
from datetime import datetime
from app.models.cart import CartItem

class OrderStatus(str, Enum):
    CREATED = "CREATED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"

class Order(BaseModel):
    id: int
    createdAt: str
    user: str
    products: List[CartItem]
    total: float
    status: OrderStatus