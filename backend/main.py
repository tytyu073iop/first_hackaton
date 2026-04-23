# filepath: backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from models import init_db, SessionLocal
from seed_data import seed_partners
from routers.game import router as game_router
from routers.auth import router as auth_router
from routers.pending import router as pending_router

app = FastAPI(title="Fog of War — MTBank")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
"*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(game_router)
app.include_router(auth_router)
app.include_router(pending_router)


@app.on_event("startup")
def on_startup():
    init_db()
    db = SessionLocal()
    try:
        print("Seeding partners...")
        seed_partners(db)
    finally:
        db.close()


@app.get("/")
def root():
    return {"service": "fog-of-war", "status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
