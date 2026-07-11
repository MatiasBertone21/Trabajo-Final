from fastapi import APIRouter, HTTPException  # <-- Agregado HTTPException
from app.core.config import settings
from app.services import auth_service, product_service
from app.models.auth import LoginRequest
from app.api import cart_endpoints, order_endpoints

router = APIRouter()

@router.get("/", tags=["General"], summary="Root endpoint", description="Verifica si el servicio está levantado")
def read_root():
    return {"service": settings.app_name, "status": "running"}

@router.get("/health", tags=["General"], summary="Health check")
def health():
    return {"status": "ok"}

@router.get("/version", tags=["General"], summary="API Version")
def get_version():
    return {"application": settings.app_name, "version": settings.version}

@router.post("/login", tags=["Auth"])
def login(credentials: LoginRequest):
    user = auth_service.authenticate_user(credentials.email, credentials.password)
    if not user:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    return {"success": True, "token": "fake-jwt-token", "user": user}

@router.get("/products", tags=["Products"])
def list_products():
    return product_service.get_all_products()

@router.get("/products/{id}", tags=["Products"])
def get_product(id: int):
    product = product_service.get_product_by_id(id)
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return product

@router.get("/categories", tags=["Products"])
def list_categories():
    return ["Electronics", "Books", "Sports", "Home", "Clothes"]

# Corrección clave aquí: usar 'router' en minúscula
router.include_router(cart_endpoints.router, prefix="/cart", tags=["Cart"])
router.include_router(order_endpoints.router, prefix="/orders", tags=["Orders"])
router.include_router(order_endpoints.router, prefix="/checkout", tags=["Checkout"])