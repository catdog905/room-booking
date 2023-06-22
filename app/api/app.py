__all__ = ["init_app"]

from fastapi import FastAPI

from .auth.router import router as auth_router
from .booking.router import router as booking_router


def init_app(app: FastAPI):
    app.include_router(auth_router, prefix="/auth")
    app.include_router(booking_router, prefix="")
