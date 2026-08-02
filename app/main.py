from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.db import Base, engine
from app.routers import admin, auth, booking, transport, verification

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name)


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"success": False, "message": str(exc.detail)})


@app.exception_handler(Exception)
async def generic_exception_handler(_: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"success": False, "message": f"Server error: {exc}"})


app.include_router(auth.router)
app.include_router(transport.router)
app.include_router(booking.router)
app.include_router(verification.router)
app.include_router(admin.router)


@app.get("/")
def health_check():
    return {"success": True, "message": "Cloud Bus Pass System API is running"}
