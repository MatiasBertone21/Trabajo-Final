import json
from pathlib import Path

class JSONRepository:
    def __init__(self, filename: str):
        self.path = Path(f"app/data/{filename}")
        if not self.path.exists():
            with open(self.path, "w") as f:
                json.dump([], f)

    def read_all(self):
        with open(self.path, "r") as f:
            return json.load(f)

    def write_all(self, data):
        with open(self.path, "w") as f:
            json.dump(data, f, indent=4)