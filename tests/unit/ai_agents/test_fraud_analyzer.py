"""Smoke tests for FraudAnalyzer."""
import pytest
from unittest.mock import patch, MagicMock
from app.ai_agents.fraud_analyzer import FraudAnalyzer, BIN_CODES, BANK_ALIASES


class TestFraudAnalyzer:
    """Test FraudAnalyzer smoke tests."""
    
    def test_bin_codes_exist(self):
        """Test BIN_CODES dictionary is populated."""
        assert len(BIN_CODES) > 0
        assert "4276" in BIN_CODES
        assert BIN_CODES["4276"] == "Сбербанк"
    
    def test_bank_aliases_exist(self):
        """Test BANK_ALIASES dictionary is populated."""
        assert len(BANK_ALIASES) > 0
        assert "сбер" in BANK_ALIASES
        assert BANK_ALIASES["сбер"] == "Сбербанк"
    
    @pytest.mark.asyncio
    async def test_analyzer_initialization(self):
        """Test analyzer initializes correctly."""
        with patch.dict("os.environ", {"USE_AI_MOCK": "true"}):
            analyzer = FraudAnalyzer()
            assert analyzer.agent_type == "FraudAnalyzer"
    
    @pytest.mark.asyncio
    async def test_check_amount_match_pass(self):
        """Test amount check passes for matching amounts."""
        analyzer = FraudAnalyzer()
        result = analyzer._check_amount_match(10000.0, 10000.0)
        assert result["passed"] is True
        assert result["score"] == 1.0
    
    @pytest.mark.asyncio
    async def test_check_amount_match_fail(self):
        """Test amount check fails for mismatched amounts."""
        analyzer = FraudAnalyzer()
        result = analyzer._check_amount_match(10000.0, 5000.0)
        assert result["passed"] is False
        assert "amount_mismatch" in result["flags"]
    
    def test_check_bin_bank_match(self):
        """Test BIN bank check works correctly."""
        analyzer = FraudAnalyzer()
        result = analyzer._check_bin_bank("4276****5678", "Сбербанк")
        assert result["passed"] is True
        assert result["score"] == 1.0
    
    def test_check_bin_bank_mismatch(self):
        """Test BIN bank check detects mismatch."""
        analyzer = FraudAnalyzer()
        result = analyzer._check_bin_bank("4276****5678", "Тинькофф")
        assert result["passed"] is False
        assert "bin_bank_mismatch" in result["flags"]
    
    def test_check_card_format_valid(self):
        """Test card format validation."""
        analyzer = FraudAnalyzer()
        result = analyzer._check_card_format("1234****5678")
        assert result["passed"] is True
    
    def test_cards_match_with_masks(self):
        """Test card matching with masked digits."""
        analyzer = FraudAnalyzer()
        assert analyzer._cards_match("1234****5678", "1234****5678") is True
        assert analyzer._cards_match("1234****5678", "1234XXXX5678") is True
        assert analyzer._cards_match("1234****5678", "9999****5678") is False
    
    def test_normalize_phone(self):
        """Test phone normalization."""
        analyzer = FraudAnalyzer()
        assert analyzer._normalize_phone("+7 (900) 123-45-67") == "79001234567"
        assert analyzer._normalize_phone("8-900-123-45-67") == "89001234567"
    
    @pytest.mark.asyncio
    async def test_process_returns_structure(self, sample_order_data, sample_payment_data):
        """Test process returns expected structure."""
        with patch.dict("os.environ", {"USE_AI_MOCK": "true"}):
            analyzer = FraudAnalyzer()
            input_data = {
                "payment_data": sample_payment_data,
                "order_data": {
                    **sample_order_data,
                    "expected_amount": sample_order_data["amount"],
                    "expected_bank": "Сбербанк",
                    "expected_card_number": "4276****5678"
                },
                "counterparty_history": {"total_trades": 5, "disputes": 0}
            }
            result = await analyzer.process(input_data)
            assert "risk_score" in result
            assert "risk_level" in result
            assert "checks" in result
            assert "recommendation" in result
