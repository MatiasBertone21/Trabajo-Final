from app.repositories.json_repo import JSONRepository

repo = JSONRepository("products.json")

def get_all_products():
    return repo.read_all()

def get_product_by_id(product_id: int):
    products = repo.read_all()
    return next((p for p in products if p["id"] == product_id), None)