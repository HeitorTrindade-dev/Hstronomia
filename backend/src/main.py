from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from src.controllers.v1.auth import router as auth_router
from src.controllers.v1.comanda import router as comanda_router
from src.controllers.v1.cozinha import router as cozinha_router
from src.controllers.v1.financeiro import router as financeiro_router
from src.controllers.v1.item import router as item_router
from src.controllers.v1.restaurante import router as restaurante_router
from src.core.config import settings

app = FastAPI(
    title="Hstronomia API",
    description="API de Gestão Operacional e Financeira para Restaurantes",
    version="0.1.0",
    debug=settings.DEBUG,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next) -> Response:
    response: Response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    return response

app.include_router(auth_router, prefix="/api/v1")
app.include_router(restaurante_router, prefix="/api/v1")
app.include_router(financeiro_router, prefix="/api/v1")
app.include_router(item_router, prefix="/api/v1")
app.include_router(comanda_router, prefix="/api/v1")
app.include_router(cozinha_router, prefix="/api/v1")


@app.get("/api/v1/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "app": "Hstronomia API",
        "version": "0.1.0",
        "environment": settings.ENVIRONMENT,
    }
