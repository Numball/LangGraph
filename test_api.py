"""Test the FastAPI endpoints."""

import sys
import json
sys.path.insert(0, r"c:\Projects\LangGraph")

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_api():
    """Test all API endpoints."""
    print("=" * 60)
    print("Testing FastAPI Endpoints")
    print("=" * 60)
    
    # Test 1: Root endpoint
    print("\n1. Testing GET /")
    response = client.get("/")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200
    
    # Test 2: Create graph
    print("\n2. Testing POST /graph/create")
    create_request = {
        "name": "TestGraph",
        "nodes": [
            {"name": "node_a", "type": "task"},
            {"name": "node_b", "type": "task"},
            {"name": "node_c", "type": "task"},
        ],
        "edges": [
            {"source": "node_a", "target": "node_b"},
            {"source": "node_b", "target": "node_c"},
        ],
    }
    response = client.post("/graph/create", json=create_request)
    print(f"   Status: {response.status_code}")
    resp_data = response.json()
    print(f"   Response: {json.dumps(resp_data, indent=2)}")
    assert response.status_code == 200
    graph_id = resp_data["graph_id"]
    
    # Test 3: Run graph
    print("\n3. Testing POST /graph/run")
    run_request = {
        "graph_id": graph_id,
        "initial_state": {"input_value": 42},
        "max_iterations": 100,
    }
    response = client.post("/graph/run", json=run_request)
    print(f"   Status: {response.status_code}")
    resp_data = response.json()
    print(f"   Response structure:")
    print(f"     - run_id: {resp_data['run_id']}")
    print(f"     - status: {resp_data['status']}")
    print(f"     - nodes executed: {len(resp_data['execution_log'])}")
    print(f"     - final_state keys: {list(resp_data['final_state'].keys())}")
    assert response.status_code == 200
    run_id = resp_data["run_id"]
    
    # Test 4: Get state
    print("\n4. Testing GET /graph/state/{run_id}")
    response = client.get(f"/graph/state/{run_id}")
    print(f"   Status: {response.status_code}")
    resp_data = response.json()
    print(f"   Response structure:")
    print(f"     - run_id: {resp_data['run_id']}")
    print(f"     - status: {resp_data['status']}")
    print(f"     - current_state keys: {list(resp_data['current_state'].keys())}")
    assert response.status_code == 200
    
    # Test 5: Test invalid run_id
    print("\n5. Testing GET /graph/state/{run_id} with invalid ID")
    response = client.get("/graph/state/invalid_id")
    print(f"   Status: {response.status_code}")
    print(f"   Expected 404: {response.status_code == 404}")
    assert response.status_code == 404
    
    print("\n" + "=" * 60)
    print("✓ All API tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_api()
    except Exception as e:
        print(f"\nX Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
