from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from db.database import init_db
from routers import subscribers, payments

# ================================================================
# APP ENTRY POINT
# Run with: python main.py
#       or: uvicorn main:app --reload
# ================================================================

app = FastAPI(
    title="MySite API",
    version="1.0.0",
    # Disable docs in production by setting these to None:
    # docs_url=None,
    # redoc_url=None,
)

# ── CORS ─────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────
app.include_router(subscribers.router, prefix="/subscribers", tags=["Subscribers"])
app.include_router(payments.router,    prefix="/payments",    tags=["Payments"])

# ── Startup ───────────────────────────────────────────────────────
@app.on_event("startup")
def on_startup():
    init_db()
    print("✓ Database initialised")
    print("✓ Server ready")


# ── Health check ─────────────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "ok"}


# ── Run directly ─────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)