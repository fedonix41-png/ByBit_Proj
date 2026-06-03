import pytest

def test_get_ads(test_client, auth_headers, mock_bybit_client):
    """Test fetching user advertisements."""
    mock_bybit_client.get_ads_list.return_value = []
    
    response = test_client.get("/api/ads", headers=auth_headers)
    
    assert response.status_code == 200
    assert response.json() == {"success": True, "data": []}
    mock_bybit_client.get_ads_list.assert_called_once()

def test_create_ad(test_client, auth_headers, mock_bybit_client):
    """Test creating a new advertisement."""
    mock_bybit_client.create_ad.return_value = "AD_NEW_123"
    
    payload = {
        "side": "BUY",
        "currency": "RUB",
        "crypto": "USDT",
        "price": 95.5,
        "min_amount": 1000.0,
        "max_amount": 50000.0,
        "payment_methods": ["1", "2"]
    }
    
    response = test_client.post("/api/ads", json=payload, headers=auth_headers)
    
    assert response.status_code == 200
    assert response.json() == {"success": True, "ad_id": "AD_NEW_123"}
    mock_bybit_client.create_ad.assert_called_once_with(
        side="BUY",
        currency="RUB",
        crypto="USDT",
        price=95.5,
        min_amount=1000.0,
        max_amount=50000.0,
        payment_methods=["1", "2"]
    )

def test_get_ad_details(test_client, auth_headers, mock_bybit_client):
    """Test fetching specific advertisement details."""
    ad_id = "AD_123"
    mock_bybit_client.get_ad_details.return_value = {"ad_id": ad_id, "price": 95.5}
    
    response = test_client.get(f"/api/ads/{ad_id}", headers=auth_headers)
    
    assert response.status_code == 200
    assert response.json() == {"success": True, "data": {"ad_id": ad_id, "price": 95.5}}
    mock_bybit_client.get_ad_details.assert_called_once_with(ad_id)

def test_delete_ad(test_client, auth_headers, mock_bybit_client):
    """Test deleting an advertisement."""
    ad_id = "AD_123"
    mock_bybit_client.cancel_order.return_value = True
    
    response = test_client.delete(f"/api/ads/{ad_id}", headers=auth_headers)
    
    assert response.status_code == 200
    assert response.json() == {"success": True, "message": "Ad deleted"}
    mock_bybit_client.cancel_order.assert_called_once_with(ad_id)
