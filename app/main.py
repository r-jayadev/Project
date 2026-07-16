from fastapi import FastAPI
import uvicorn
from app.config import settings
from app.database import Base, engine
from app.routers import router

#Create all tables
Base.metadata.create_all(bind=engine)

#Create FastAPI Application
app=FastAPI(title="Dockerized Data Pipeline",
            description="API for uploading, processing and analyzing employee data",
            version="1.0.0")

#Register Routes
app.include_router(router)

@app.get("/")
def home():
    """
    Home endpoints
    """
    return {
        "Message": "Docekerized Data Pipeline"
    }

if __name__=="__main__":
    uvicorn.run("app.main:app",
                host=settings.API_HOST,
                port=settings.API_PORT,
                reload=settings.DEBUG)




