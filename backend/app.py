from fastapi import FastAPI
from backend.routing import router


app = FastAPI()

app.include_router(router)
