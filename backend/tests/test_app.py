#!/usr/bin/env python3
"""
Quick test script to verify the Legal AI System FastAPI application setup
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

async def test_app_setup():
    """Test that the application can be imported and initialized"""
    
    try:
        print("🧪 Testing Legal AI System FastAPI Application Setup...")
        print("=" * 60)
        
        # Test core module imports
        print("1. Testing core module imports...")
        from app.src.core import (
            get_settings,
            app,
            health_router,
            get_logger,
            LegalAIException,
            configure_middleware
        )
        print("   ✅ Core modules imported successfully")
        
        # Test settings
        print("\n2. Testing configuration...")
        settings = get_settings()
        print(f"   📋 App Name: {settings.APP_NAME}")
        print(f"   📋 Version: {getattr(settings, 'APP_VERSION', '1.0.0')}")
        print(f"   📋 Environment: {settings.ENVIRONMENT}")
        print(f"   📋 Debug Mode: {settings.DEBUG}")
        print("   ✅ Configuration loaded successfully")
        
        # Test logger
        print("\n3. Testing logging system...")
        logger = get_logger('test')
        logger.info("Test log message")
        print("   ✅ Logging system working")
        
        # Test app instance
        print("\n4. Testing FastAPI application...")
        print(f"   📋 App Title: {app.title}")
        print(f"   📋 App Version: {app.version}")
        print(f"   📋 Routes Count: {len(app.routes)}")
        print("   ✅ FastAPI application configured")
        
        # Test exception handling
        print("\n5. Testing exception system...")
        try:
            raise LegalAIException("Test exception", error_code="TEST_ERROR")
        except LegalAIException as e:
            print(f"   📋 Exception caught: {e.error_code} - {e.message}")
            print("   ✅ Exception handling working")
        
        print("\n" + "=" * 60)
        print("🎉 All tests passed! Legal AI System is ready to run.")
        print("\nTo start the server, run:")
        print("   cd backend && python main.py")
        print("\nOr using uvicorn directly:")
        print("   cd backend && uvicorn main:app --reload")
        print("\nHealth check endpoint will be available at:")
        print("   http://localhost:8000/health")
        print("   http://localhost:8000/docs (API documentation)")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("\nPlease ensure all dependencies are installed:")
        print("   pip install -r requirements.txt")
        return False
        
    except Exception as e:
        print(f"❌ Setup Error: {e}")
        print(f"   Error Type: {type(e).__name__}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_app_setup())
    sys.exit(0 if success else 1)