import pytest

def test_get_chat(test_client, auth_headers, mock_bybit_client):
    """Test fetching chat messages for an order."""
    order_id = "ORD_123"
    mock_bybit_client.get_chat_messages.return_value = []
    
    response = test_client.get(f"/api/chat/{order_id}", headers=auth_headers)
    
    assert response.status_code == 200
    assert response.json() == {"success": True, "data": []}
    mock_bybit_client.get_chat_messages.assert_called_once_with(order_id)

def test_send_chat_message(test_client, auth_headers, mock_bybit_client):
    """Test sending a chat message for an order."""
    order_id = "ORD_123"
    mock_bybit_client.send_chat_message.return_value = True
    
    payload = {
        "text": "Hello, this is a test message"
    }
    
    response = test_client.post(f"/api/chat/{order_id}/send", json=payload, headers=auth_headers)
    
    assert response.status_code == 200
    assert response.json() == {"success": True, "message": "Message sent"}
    mock_bybit_client.send_chat_message.assert_called_once_with(order_id, payload["text"])
