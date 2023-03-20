from app.core.config import settings
from app.core.logger import logger
from app.factory import create_app

app = create_app()

if __name__ == "__main__":
    import uvicorn

    logger.info("Starting uvicorn in reload mode")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        reload=True,
        port=settings.PORT,
    )
