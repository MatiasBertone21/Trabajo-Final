from app.repositories.json_repo import JSONRepository

repo = JSONRepository("users.json")

def authenticate_user(email, password):
    users = repo.read_all()
    for user in users:
        # Comparamos directamente el email y la contraseña en texto plano
        if user["email"] == email and user["password"] == password:
            return {"id": user["id"], "email": user["email"]}
    return None