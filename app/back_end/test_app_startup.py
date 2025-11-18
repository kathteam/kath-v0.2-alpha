#!/usr/bin/env python3
"""Test application startup and basic functionality."""

import sys

print("=" * 80)
print("Testing Application Startup")
print("=" * 80)

# Test 1: Import application
print("\n1. Testing imports...")
try:
    from src import create_app

    print("    Flask app imports successfully")
except Exception as e:
    print(f"    Failed to import: {e}")
    sys.exit(1)

# Test 2: Create app
print("\n2. Creating Flask application...")
try:
    app = create_app()
    print("    Flask app created successfully")
except Exception as e:
    print(f"    Failed to create app: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

# Test 3: Check routes
print("\n3. Checking registered routes...")
with app.app_context():
    routes = []
    for rule in app.url_map.iter_rules():
        if not rule.endpoint.startswith("static"):
            routes.append(f"   {rule.endpoint:40s} {rule.rule}")

    print(f"    Registered {len(routes)} routes")

    # Check for monitoring routes
    monitoring_routes = [r for r in routes if "monitoring" in r]
    if monitoring_routes:
        print(f"    Monitoring routes found: {len(monitoring_routes)}")
        for route in monitoring_routes:
            print(f"      {route}")

# Test 4: Check database
print("\n4. Testing database connection...")
try:
    from sqlalchemy import create_engine, text

    from src.database.config import get_database_uri

    uri = get_database_uri()
    engine = create_engine(uri)

    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM variants")).scalar()
        print(f"    Database connected: {result:,} variants")

        result = conn.execute(text("SELECT COUNT(*) FROM workspaces")).scalar()
        print(f"    Workspaces: {result}")

        result = conn.execute(text("SELECT COUNT(*) FROM files")).scalar()
        print(f"    Files: {result}")
except Exception as e:
    print(f"    Database error: {e}")
    sys.exit(1)

# Test 5: Test request
print("\n5. Testing HTTP request...")
try:
    with app.test_client() as client:
        # Test health endpoint
        response = client.get("/api/v1/monitoring/health")
        print(f"   Health check: {response.status_code}")
        if response.status_code == 200:
            data = response.get_json()
            print(f"    Status: {data.get('status')}")
            print(f"    Database: {data.get('database')}")
except Exception as e:
    print(f"    Request failed: {e}")
    import traceback

    traceback.print_exc()

# Test 6: Test database service
print("\n6. Testing database service...")
try:
    from src.services import WorkspaceService

    service = WorkspaceService()
    print("    WorkspaceService instantiated")

    # Check if file exists
    exists = service.file_exists("template", "template/template_3000.csv")
    if exists:
        print("    File lookup working")
    else:
        print("   ! File not found (might need different path)")

except Exception as e:
    print(f"    Service error: {e}")
    import traceback

    traceback.print_exc()

print("\n" + "=" * 80)
print("Application Startup Tests Complete!")
print("=" * 80)
