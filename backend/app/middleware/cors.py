
# Auto-generated CORS middleware
from fastapi.middleware.cors import CORSMiddleware

def setup_cors(app):
    """Setup CORS middleware with secure configuration"""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=['http://localhost:3000', 'http://localhost:3001', 'https://localhost:3000', 'https://localhost:3001'],
        allow_credentials=True,
        allow_methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
        allow_headers=['Content-Type', 'Authorization', 'X-Requested-With', 'Accept', 'Origin', 'X-Session-ID'],
        max_age=3600
    )

    return app
