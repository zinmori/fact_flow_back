from fastapi import FastAPI
from app.routes import router

app = FastAPI(title="FactFlow Backend")

app.include_router(router)


@app.get("/ping")
def ping():
    return {"message": "pong"}
