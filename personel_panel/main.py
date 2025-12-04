# main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import os
import json

# Bu dosyanın olduğu klasör
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# JSON ve HTML dosyalarının TAM yolu
DATA_FILE = os.path.join(BASE_DIR, "personel_data.json")
HTML_FILE = os.path.join(BASE_DIR, "personeltakip.html")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def load_data():
    """JSON dosyasını oku, yoksa temel yapı ile oluştur."""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
    else:
        data = {}

    # Temel alanları garantiye al
    if "employees" not in data:
        data["employees"] = []
    if "admins" not in data:
        data["admins"] = []
    if "weeks" not in data:
        data["weeks"] = []
    if "users" not in data:
        data["users"] = []

    # Eğer hiç admin yoksa, varsayılan admin (admin / 1234) oluştur
    has_admin = any(u.get("role") == "admin" for u in data["users"])
    if not has_admin:
        default_admin_user = {
            "id": "user_admin_default",
            "username": "admin",
            "password": "1234",  # İstersen panelden değiştirirsin
            "role": "admin",
        }
        data["users"].append(default_admin_user)

        if not any(a.get("username") == "admin" for a in data["admins"]):
            default_admin = {
                "id": "adm_default",
                "name": "Varsayılan Admin",
                "username": "admin",
            }
            data["admins"].append(default_admin)

    save_data(data)
    return data


def save_data(data: dict):
    """JSON dosyasını kaydet."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class LoginRequest(BaseModel):
    username: str
    password: str


@app.get("/")
async def index():
    """Panelin HTML dosyasını döndür."""
    # Burada TAM yol kullanıyoruz, Render'da hata olmaması için
    if not os.path.exists(HTML_FILE):
        raise RuntimeError(f"HTML dosyası bulunamadı: {HTML_FILE}")
    return FileResponse(HTML_FILE)


@app.get("/api/state")
async def get_state():
    data = load_data()
    return JSONResponse(content=data)


@app.post("/api/state")
async def set_state(new_state: dict):
    """
    Frontend state'i komple gönderiyor (employees, admins, weeks, users).
    Bunu JSON'a kaydediyoruz.
    """
    if not isinstance(new_state, dict):
        raise HTTPException(status_code=400, detail="Geçersiz veri")
    save_data(new_state)
    return {"status": "ok"}


@app.post("/api/login")
async def login(payload: LoginRequest):
    data = load_data()
    username = payload.username.strip()
    password = payload.password.strip()

    user = next(
        (u for u in data["users"] if u.get("username") == username and u.get("password") == password),
        None,
    )

    if not user:
        return {"status": "error", "message": "Kullanıcı adı veya şifre hatalı."}

    return {
        "status": "ok",
        "username": user["username"],
        "role": user.get("role", "employee"),
    }
