from fastapi import FastAPI
from .auth.router import router as auth_router
from .booking.router import router as booking_router

app = FastAPI(
    title="Room Booking Service",
    version="0.1.0",
    description="Innopolis University room booking service API.",
)

app.include_router(auth_router, prefix="/auth")
app.include_router(booking_router, prefix="")
