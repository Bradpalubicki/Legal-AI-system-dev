#!/usr/bin/env python3
"""
Debug script to test router imports and diagnose issues.
"""

import sys
import traceback
from pathlib import Path

def test_router_import(module_path, router_name="router"):
    """Test importing a router from a module and show detailed information."""
    print(f"\n{'='*60}")
    print(f"Testing import: from {module_path} import {router_name}")
    print(f"{'='*60}")

    try:
        # Try to import the module
        module = __import__(module_path, fromlist=[router_name])
        print(f"[OK] Module '{module_path}' imported successfully")

        # Check what's available in the module
        available_attrs = [attr for attr in dir(module) if not attr.startswith('_')]
        print(f"Available attributes: {available_attrs}")

        # Try to get the router
        if hasattr(module, router_name):
            router = getattr(module, router_name)
            print(f"[OK] Router '{router_name}' found in module")
            print(f"Router type: {type(router)}")
            print(f"Router class: {router.__class__.__name__}")

            # Check if it's a FastAPI router
            try:
                from fastapi import APIRouter
                if isinstance(router, APIRouter):
                    print(f"[OK] Router is a valid FastAPI APIRouter instance")
                    print(f"Number of routes: {len(router.routes)}")
                    if router.routes:
                        print(f"Routes:")
                        for route in router.routes:
                            if hasattr(route, 'path') and hasattr(route, 'methods'):
                                methods = getattr(route, 'methods', set())
                                print(f"   - {route.path} [{', '.join(methods)}]")
                    else:
                        print(f"[WARNING] Router has no routes defined")
                else:
                    print(f"[ERROR] Router is not a FastAPI APIRouter instance")
            except ImportError as e:
                print(f"[WARNING] Cannot verify router type (FastAPI not available): {e}")

        else:
            print(f"[ERROR] Router '{router_name}' not found in module")
            print(f"Try one of these instead: {available_attrs}")

    except ImportError as e:
        print(f"[ERROR] Import failed: {e}")
        print(f"Full traceback:")
        traceback.print_exc()

        # Try to diagnose the issue
        module_parts = module_path.split('.')
        print(f"\nDiagnosing import path...")

        current_path = ""
        for i, part in enumerate(module_parts):
            if i == 0:
                current_path = part
            else:
                current_path += f".{part}"

            try:
                test_module = __import__(current_path)
                print(f"   [OK] {current_path}")
            except ImportError as e:
                print(f"   [ERROR] {current_path} - FAILED: {e}")
                break

        # Check if file exists
        file_path = Path(*module_parts[:-1], f"{module_parts[-1]}.py")
        if file_path.exists():
            print(f"File exists at: {file_path}")
        else:
            print(f"File not found at: {file_path}")
            # Check for __init__.py
            init_path = Path(*module_parts, "__init__.py")
            if init_path.exists():
                print(f"Package found at: {init_path}")

    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        traceback.print_exc()

def main():
    """Main function to test all router imports."""
    print("Legal AI System - Router Import Debug Script")
    print(f"Current working directory: {Path.cwd()}")
    print(f"Python path: {sys.path}")

    # Test each router
    routers_to_test = [
        ("src.api.document_processing", "router"),
        ("src.api.bankruptcy", "router"),
    ]

    for module_path, router_name in routers_to_test:
        test_router_import(module_path, router_name)

    # Additional checks
    print(f"\n{'='*60}")
    print("Additional Checks")
    print(f"{'='*60}")

    # Check if src directory exists
    src_path = Path("src")
    if src_path.exists():
        print(f"[OK] src directory exists")
        api_path = src_path / "api"
        if api_path.exists():
            print(f"[OK] src/api directory exists")

            # List contents of src/api
            api_contents = list(api_path.iterdir())
            print(f"Contents of src/api:")
            for item in api_contents:
                print(f"   - {item.name} ({'dir' if item.is_dir() else 'file'})")
        else:
            print(f"[ERROR] src/api directory not found")
    else:
        print(f"[ERROR] src directory not found")

    print(f"\nDebug script completed!")

if __name__ == "__main__":
    main()