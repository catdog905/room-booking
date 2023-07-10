__all__ = ["init_app"]

from fastapi import FastAPI

from .booking.router import router as booking_router
from .iam.router import router as iam_router


def init_app(app: FastAPI):
    app.include_router(iam_router, prefix="/auth")
    app.include_router(booking_router, prefix="")
