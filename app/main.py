from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def ping() -> str:
    return "pong"
