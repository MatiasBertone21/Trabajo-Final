import json
import os
from pathlib import Path

def init_data_files():
    data_dir = Path("app/data")
    data_dir.mkdir(exist_ok=True)
    
    files = ["products.json", "users.json", "categories.json", "orders.json", "cart.json"]
    
    for file_name in files:
        file_path = data_dir / file_name
        if not file_path.exists():
            with open(file_path, "w") as f:
                json.dump({}, f)