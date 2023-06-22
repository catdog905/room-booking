from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.config import config, Environment
from app.api.app import init_app

DEBUG = config.environment == Environment.DEVELOPMENT

app = FastAPI(
    debug=DEBUG,
    title=config.app_title,
    version=config.app_version,
    description=config.app_description,
    openapi_url="/openapi.json" if DEBUG else None,
    docs_url="/docs" if DEBUG else None,
    redoc_url="/redoc" if DEBUG else None,
)

if config.cors_allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in config.cors_allowed_origins],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

init_app(app)


@app.on_event("startup")
async def startup():
    # Wire-up all dependencies here
    ...


@app.on_event("shutdown")
async def shutdown():
    ...
