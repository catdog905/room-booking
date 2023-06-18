from app.api.app import app


@app.on_event("startup")
async def startup():
    # Wire-up all dependencies here
    ...


@app.on_event("shutdown")
async def shutdown():
    ...
