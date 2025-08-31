
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routes.main import router
from app.routes.users import router as users_router
import os


app = FastAPI(title="FactFlow Backend - Fact Checking with Community & AI")

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # À restreindre en prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for uploaded content
uploads_dir = "uploads"
if not os.path.exists(uploads_dir):
    os.makedirs(uploads_dir)

app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

# Include routers
app.include_router(router)  # Main routes (analyze, vote, etc.)
app.include_router(users_router)  # User management routes


@app.get("/")
def root():
    return {
        "message": "FactFlow Backend API",
        "version": "1.0.0",
        "description": "AI-powered fact checking with community validation",
        "endpoints": {
            "analyze": "POST /analyze - Analyze text for fact-checking",
            "vote": "POST /vote - Vote on article credibility",
            "users": "User management under /users/*",
            "docs": "API documentation at /docs"
        }
    }


@app.get("/ping")
def ping():
    return {"message": "pong"}
