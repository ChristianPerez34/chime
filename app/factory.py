from app.core.config import settings
from app.api import api_router
from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_PATH}/openapi.json",
        docs_url="/docs/",
        description="Chime Rest API",
        redoc_url=None,
    )
    setup_routers(app=app)
    return app


def setup_routers(app: FastAPI) -> None:
    app.include_router(api_router, prefix=settings.API_PATH)
