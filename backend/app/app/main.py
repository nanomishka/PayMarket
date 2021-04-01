from fastapi import FastAPI

from app.api.routers import api_router

app = FastAPI()
app.include_router(api_router)
