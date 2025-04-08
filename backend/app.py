from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routing import router


app = FastAPI()

origins = [
    'http://127.0.0.1:9000',
    'https://127.0.0.1:9000',
    'http://localhost:9000',
    'https://localhost:9000',
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(router)
