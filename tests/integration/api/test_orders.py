import pytest

def test_get_orders(test_client, auth_headers, mock_bybit_client):
    """Test fetching all orders."""
    mock_bybit_client.get_orders.return_value = []
    
    response = test_client.get("/api/orders?page=1&size=20", headers=auth_headers)
    
    assert response.status_code == 200
    assert response.json() == {"success": True, "data": [], "page": 1, "size": 20}
    mock_bybit_client.get_orders.assert_called_once_with(page=1, size=20)

def test_get_order_details(test_client, auth_headers, mock_bybit_client):
    """Test fetching specific order details."""
    order_id = "ORD_123"
    mock_bybit_client.get_order_details.return_value = {"order_id": order_id, "status": "pending"}
    
    response = test_client.get(f"/api/order/{order_id}", headers=auth_headers)
    
    assert response.status_code == 200
    assert response.json() == {"success": True, "data": {"order_id": order_id, "status": "pending"}}
    mock_bybit_client.get_order_details.assert_called_once_with(order_id)

def test_cancel_order(test_client, auth_headers, mock_bybit_client):
    """Test cancelling an order."""
    order_id = "ORD_123"
    mock_bybit_client.cancel_order.return_value = True
    
    response = test_client.post(f"/api/order/{order_id}/cancel", headers=auth_headers)
    
    assert response.status_code == 200
    assert response.json() == {"success": True, "message": "Order cancelled"}
    mock_bybit_client.cancel_order.assert_called_once_with(order_id)

def test_mark_order_paid(test_client, auth_headers, mock_bybit_client):
    """Test marking an order as paid."""
    order_id = "ORD_123"
    mock_bybit_client.mark_as_paid.return_value = True
    
    payload = {
        "payment_type": "BANK_TRANSFER",
        "payment_id": "PAY_123"
    }
    
    response = test_client.post(f"/api/order/{order_id}/mark_paid", json=payload, headers=auth_headers)
    
    assert response.status_code == 200
    assert response.json() == {"success": True, "message": "Order marked as paid"}
    mock_bybit_client.mark_as_paid.assert_called_once_with(
        order_id=order_id,
        payment_type="BANK_TRANSFER",
        payment_id="PAY_123"
    )

def test_release_order_assets(test_client, auth_headers, mock_bybit_client):
    """Test releasing assets for an order."""
    order_id = "ORD_123"
    mock_bybit_client.release_assets.return_value = True
    
    response = test_client.post(f"/api/order/{order_id}/release", headers=auth_headers)
    
    assert response.status_code == 200
    assert response.json() == {"success": True, "message": "Assets released"}
    mock_bybit_client.release_assets.assert_called_once_with(order_id)
