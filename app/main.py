from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import api_router


def create_application() -> FastAPI:
    """Create and configure FastAPI application"""
    application = FastAPI(
        openapi_url=f"/api/v1",
    )

    # Configure CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API router
    application.include_router(
        api_router,
        prefix=f"/api/v1"
    )

    return application


# Create FastAPI app instance
app = create_application()


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy"
    }
