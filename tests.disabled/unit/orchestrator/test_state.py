"""Smoke tests for orchestrator state."""
import pytest
from app.orchestrator.state import P2PAutomationState


class TestP2PAutomationState:
    """Test P2PAutomationState TypedDict."""
    
    def test_state_has_required_fields(self):
        """Test state has all required fields."""
        state = P2PAutomationState(
            order_id="TEST-123",
            order_data={"amount": 10000, "currency": "RUB"},
            messages=[],
            last_message=None,
            conversation_history=[],
            message_count=0,
            session_start=None,
            input_type=None,
            has_image=False,
            has_voice=False,
            image_analysis=None,
            voice_transcription=None,
            intent=None,
            intent_confidence=None,
            entities=None,
            response_type=None,
            routing=None,
            proposed_response=None,
            response_tone=None,
            payment_proof_path=None,
            payment_data=None,
            risk_score=None,
            risk_level=None,
            risk_flags=None,
            risk_checks=None,
            processing_id=None,
            processing_status=None,
            response_approval_required=False,
            response_approved=None,
            risk_approval_required=False,
            risk_approved=None,
            user_id=None,
            username=None,
            user_context=None,
            run_id=None,
            error=None,
            current_step=None,
            extra_metadata=None
        )
        assert state["order_id"] == "TEST-123"
        assert state["order_data"]["amount"] == 10000
    
    def test_state_with_intent_classification(self):
        """Test state with intent classification data."""
        state = P2PAutomationState(
            order_id="TEST-456",
            messages=[{"text": "Хочу купить USDT", "sender": "counterparty"}],
            last_message={"text": "Хочу купить USDT", "sender": "counterparty"},
            intent="BUY_CRYPTO",
            intent_confidence=0.95,
            entities={"crypto": "USDT", "amount": 100},
            message_count=1,
            has_image=False,
            has_voice=False,
            response_approval_required=False,
            risk_approval_required=False
        )
        assert state["intent"] == "BUY_CRYPTO"
        assert state["intent_confidence"] == 0.95
        assert state["entities"]["crypto"] == "USDT"
    
    def test_state_with_risk_analysis(self):
        """Test state with risk analysis data."""
        state = P2PAutomationState(
            order_id="TEST-789",
            payment_proof_path="/proofs/payment.png",
            payment_data={"amount": 10000, "currency": "RUB", "confidence": 0.98},
            risk_score=0.15,
            risk_level="LOW",
            risk_flags=[],
            risk_checks={"amount_match": True, "name_match": True},
            message_count=0,
            has_image=True,
            has_voice=False,
            response_approval_required=False,
            risk_approval_required=True,
            risk_approved=True
        )
        assert state["risk_score"] == 0.15
        assert state["risk_level"] == "LOW"
        assert state["risk_checks"]["amount_match"] is True
        assert state["risk_approved"] is True
