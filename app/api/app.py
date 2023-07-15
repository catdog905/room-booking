__all__ = ["init_app"]

from fastapi import FastAPI

from .booking.bearer_booking_router import router as user_booking_router
from .booking.integration_router import router as integration_router
from .booking.common_router import router as common_router
from .iam.router import router as iam_router


def init_app(app: FastAPI):
    app.include_router(iam_router, prefix="/auth")
    app.include_router(user_booking_router, prefix="/bearer")
    app.include_router(integration_router, prefix="/integration")
    app.include_router(common_router, prefix="/common")
