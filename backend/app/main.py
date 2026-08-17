import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.auth.routes import router as auth_router
from app.chat.routes import router as chat_router
from app.config import get_settings
from app.documents.routes import router as documents_router
from app.mastery.routes import router as mastery_router
from app.practice.routes import router as practice_router
from app.services.openrouter_client import OpenRouterError
from app.teachback.routes import router as teachback_router
from app.topics.routes import router as topics_router

logger = logging.getLogger("bodhi")

settings = get_settings()

app = FastAPI(title="Bodhi API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(documents_router)
app.include_router(topics_router)
app.include_router(chat_router)
app.include_router(teachback_router)
app.include_router(practice_router)
app.include_router(mastery_router)


def _cors_headers(request: Request) -> dict[str, str]:
    """A handler registered for the base Exception class is wired by
    Starlette into ServerErrorMiddleware specifically, which sits *outside*
    CORSMiddleware — so that response never gets CORS headers added
    automatically, and a browser reports what is really a server error as a
    misleading CORS failure. Add the header by hand instead of relying on
    middleware ordering."""
    origin = request.headers.get("origin")
    if origin and origin in settings.cors_origin_list:
        return {"Access-Control-Allow-Origin": origin, "Vary": "Origin"}
    return {}


@app.exception_handler(OpenRouterError)
async def openrouter_error_handler(request: Request, exc: OpenRouterError) -> JSONResponse:
    logger.warning("OpenRouter error on %s: %s", request.url.path, exc)
    return JSONResponse(status_code=502, content={"detail": str(exc)}, headers=_cors_headers(request))


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Something went wrong. Please try again."},
        headers=_cors_headers(request),
    )


@app.get("/health")
def health():
    return {"status": "ok"}
