import pytest
import asyncio
from unittest.mock import patch

def test_start_monitor(test_client, auth_headers):
    """Test starting the AI monitor for an order."""
    order_id = "ORD_123"
    payload = {
        "order_id": order_id
    }
    
    # We mock asyncio.create_task to avoid actually running the graph in the background
    with patch("asyncio.create_task") as mock_create_task:
        response = test_client.post("/api/start_monitor", json=payload, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["order_id"] == order_id
        assert "run_id" in data
        mock_create_task.assert_called_once()

def test_get_runs(test_client, auth_headers):
    """Test getting active runs."""
    response = test_client.get("/api/runs", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
