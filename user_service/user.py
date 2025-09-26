from fastapi import FastAPI

app = FastAPI(title="User Service")

users = [
    {"id": 1, "name": "Ashish"},
    {"id": 2, "name": "Lama"},
]

@app.get("/users")
def get_users():
    return {"users": users}

@app.get("/users/{user_id}")
def get_user(user_id: int):
    user = next((u for u in users if u["id"] == user_id), None)
    return {"user": user} if user else {"error": "User not found"}