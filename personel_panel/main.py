# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import json
import os

DATA_FILE = "personel_data.json"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
    else:
        data = {}

    # Temel alan garantileri
    if "employees" not in data:
        data["employees"] = []
    if "admins" not in data:
        data["admins"] = []
    if "weeks" not in data:
        data["weeks"] = []
    if "users" not in data:
        data["users"] = []

    # Varsayılan admin yoksa oluştur (admin / 1234)
    has_admin = any(u.get("role") == "admin" for u in data["users"])
    if not has_admin:
        default_admin = {
            "id": "user_admin_default",
            "username": "admin",
            "password": "1234",
            "role": "admin",
        }
        data["users"].append(default_admin)

        if not any(a.get("username") == "admin" for a in data["admins"]):
            data["admins"].append(
                {"id": "adm_admin_default", "name": "Sistem Admin", "username": "admin"}
            )

    return data


def save_data(data: dict):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@app.get("/")
def root():
    return FileResponse("personeltakip.html")


@app.get("/api/state")
def get_state():
    return load_data()


@app.post("/api/state")
async def set_state(payload: dict):
    save_data(payload)
    return {"status": "ok"}


@app.post("/api/login")
async def login(payload: dict):
    username = payload.get("username", "")
    password = payload.get("password", "")

    data = load_data()

    for user in data["users"]:
        if user["username"] == username and user["password"] == password:
            return {
                "status": "ok",
                "username": username,
                "role": user["role"],
            }

    return {
        "status": "error",
        "message": "Kullanıcı adı veya şifre hatalı."
    }
