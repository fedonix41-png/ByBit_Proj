"""Processing API client."""
from loguru import logger
import os
import httpx
from typing import Dict, Any, Optional

class ProcessingClient:
    """Client for external processing API."""
    
    def __init__(self, base_url: str = None, api_key: str = None, use_mock: bool = True):
        self.base_url = base_url or os.getenv("PROCESSING_API_URL", "https://api.processing.example.com")
        self.api_key = api_key or os.getenv("PROCESSING_API_KEY", "")
        self.use_mock = use_mock or not self.api_key
        
        if not self.use_mock:
            self.client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=30.0
            )
        
        logger.info(f"ProcessingClient initialized (mock={self.use_mock})")
    
    async def submit_transaction(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit transaction to processing.
        
        Args:
            transaction_data: {
                "order_id": "ORD123",
                "amount": 10000.0,
                "currency": "RUB",
                "card_number": "1234****5678",
                "payment_proof_url": "https://...",
                "extra_metadata": {}
            }
        
        Returns:
            {
                "processing_id": "TXN456",
                "status": "pending",
                "estimated_completion": "2024-01-15T15:00:00Z"
            }
        """
        if self.use_mock:
            return await self._mock_submit(transaction_data)
        
        try:
            response = await self.client.post(
                "/api/v1/transactions",
                json=transaction_data
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Transaction submitted: {result.get('processing_id')}")
            return result
        
        except httpx.HTTPError as e:
            logger.error(f"Processing API error: {e}")
            raise
    
    async def check_status(self, processing_id: str) -> Dict[str, Any]:
        """
        Check transaction status.
        
        Returns:
            {
                "processing_id": "TXN456",
                "status": "completed",
                "completed_at": "2024-01-15T15:00:00Z"
            }
        """
        if self.use_mock:
            return await self._mock_status(processing_id)
        
        try:
            response = await self.client.get(f"/api/v1/transactions/{processing_id}")
            response.raise_for_status()
            return response.json()
        
        except httpx.HTTPError as e:
            logger.error(f"Status check error: {e}")
            raise
    
    async def cancel_transaction(self, processing_id: str) -> bool:
        """Cancel transaction."""
        if self.use_mock:
            logger.info(f"[MOCK] Cancelling transaction {processing_id}")
            return True
        
        try:
            response = await self.client.post(f"/api/v1/transactions/{processing_id}/cancel")
            response.raise_for_status()
            return True
        
        except httpx.HTTPError as e:
            logger.error(f"Cancel error: {e}")
            return False
    
    async def handle_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle webhook from processing.
        
        Args:
            webhook_data: {
                "processing_id": "TXN456",
                "status": "completed",
                "signature": "..."
            }
        """
        # Validate signature
        if not self._validate_signature(webhook_data):
            raise ValueError("Invalid webhook signature")
        
        logger.info(f"Webhook received: {webhook_data.get('processing_id')} - {webhook_data.get('status')}")
        
        return {
            "processing_id": webhook_data.get("processing_id"),
            "status": webhook_data.get("status"),
            "validated": True
        }
    
    def _validate_signature(self, webhook_data: Dict[str, Any]) -> bool:
        """Validate webhook signature."""
        # TODO: Implement actual signature validation
        return True
    
    async def _mock_submit(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock transaction submission."""
        import time
        processing_id = f"TXN{int(time.time())}"
        
        logger.info(f"[MOCK] Transaction submitted: {processing_id}")
        
        return {
            "processing_id": processing_id,
            "status": "pending",
            "estimated_completion": "2024-01-15T15:00:00Z",
            "mock": True
        }
    
    async def _mock_status(self, processing_id: str) -> Dict[str, Any]:
        """Mock status check."""
        logger.info(f"[MOCK] Checking status: {processing_id}")
        
        return {
            "processing_id": processing_id,
            "status": "completed",
            "completed_at": "2024-01-15T15:00:00Z",
            "mock": True
        }

# Global instance
processing_client = ProcessingClient(use_mock=True)
