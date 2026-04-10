from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.exceptions import HTTPException as FastAPIHTTPException
from fastapi.middleware.cors import CORSMiddleware
from logging import getLogger

from backend.app.core.config import settings
from backend.app.core.errors import api_exception_handler, global_exception_handler, http_exception_handler
from backend.app.core.exceptions import APIException
from backend.app.infrastructure.database import init_database
from backend.app.infrastructure.repositories import repository_session
from backend.app.routers import auth, news, config, pipeline
from backend.app.services.scraper_runtime_state_service import scraper_runtime_state_service

logger = getLogger("uvicorn")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        init_database()
        scraper_runtime_state_service.ensure_runtime_initialized()
        logger.info("Database initialized")
        yield
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        yield
    finally:
        logger.info("Shutting down...")


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(APIException, api_exception_handler)
app.add_exception_handler(FastAPIHTTPException, http_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)


@app.middleware("http")
async def bind_repository_session(request, call_next):
    with repository_session():
        return await call_next(request)

app.include_router(auth.router, prefix="/api", tags=["Auth"])
app.include_router(news.router, prefix="/api", tags=["News"])
app.include_router(config.router, prefix="/api", tags=["Config"])
app.include_router(pipeline.router, prefix="/api", tags=["Pipeline"])


@app.get("/")
def health_check():
    return {"status": "ok", "version": "2.0.0-modular"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
