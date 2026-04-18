from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

def register_middleware(app: FastAPI):
    """Register all middleware"""
    
    # CORS middleware - temporarily allow all for testing
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Change to "*" for testing
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Optional: Remove TrustedHostMiddleware if it causes issues
    # app.add_middleware(
    #     TrustedHostMiddleware,
    #     allowed_hosts=["*"]  # Allow all hosts
    # )
    
    return app