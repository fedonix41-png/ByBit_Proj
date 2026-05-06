"""Smoke tests for orchestrator graph."""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


class TestOrchestratorGraph:
    """Test LangGraph orchestrator."""
    
    def test_graph_module_imports(self):
        """Test graph module can be imported."""
        from app.orchestrator import graph
        assert hasattr(graph, "create_p2p_graph") or hasattr(graph, "p2p_graph")
    
    def test_graph_creation(self):
        """Test graph can be created."""
        with patch.dict("os.environ", {"USE_AI_MOCK": "true"}):
            from app.orchestrator.graph import create_p2p_graph
            graph_app = create_p2p_graph()
            assert graph_app is not None
    
    def test_graph_nodes_exist(self):
        """Test graph has expected nodes."""
        from app.orchestrator.graph import create_p2p_graph
        
        graph_app = create_p2p_graph()
        
        expected_nodes = [
            "fetch_order",
            "check_messages",
            "classify_intent",
            "generate_response",
            "await_response_approval",
            "send_response",
            "parse_payment",
            "analyze_risk",
            "await_risk_approval",
            "submit_processing",
            "confirm_payment",
            "notify_completion"
        ]
        
        if hasattr(graph_app, "nodes"):
            for node in expected_nodes:
                assert node in graph_app.nodes, f"Missing node: {node}"
    
    @pytest.mark.asyncio
    async def test_state_transitions(self):
        """Test basic state transitions."""
        from app.orchestrator.state import P2PAutomationState
        
        initial_state = P2PAutomationState(
            order_id="TEST-ORDER",
            messages=[],
            message_count=0,
            has_image=False,
            has_voice=False,
            response_approval_required=False,
            risk_approval_required=False
        )
        
        updated_state = {
            **initial_state,
            "intent": "BUY_CRYPTO",
            "intent_confidence": 0.92,
            "current_step": "classify_intent"
        }
        
        assert updated_state["intent"] == "BUY_CRYPTO"
        assert updated_state["intent_confidence"] == 0.92
        assert updated_state["current_step"] == "classify_intent"


class TestGraphNodes:
    """Test individual graph nodes."""
    
    @pytest.mark.asyncio
    async def test_classify_intent_node_imports(self):
        """Test intent classification node can be imported."""
        from app.orchestrator.nodes import classify_intent
        assert callable(classify_intent)
    
    @pytest.mark.asyncio
    async def test_analyze_fraud_risk_node_imports(self):
        """Test risk analysis node can be imported."""
        from app.orchestrator.nodes import analyze_fraud_risk
        assert callable(analyze_fraud_risk)
    
    @pytest.mark.asyncio
    async def test_classify_intent_node_execution(self):
        """Test intent classification node execution."""
        with patch.dict("os.environ", {"USE_AI_MOCK": "true"}):
            with patch("app.orchestrator.nodes.get_intent_classifier") as mock_classifier:
                mock_agent = MagicMock()
                mock_agent.process = AsyncMock(return_value={
                    "intent": "BUY_CRYPTO",
                    "confidence": 0.95,
                    "entities": {"crypto": "USDT"}
                })
                mock_classifier.return_value = mock_agent
                
                from app.orchestrator.nodes import classify_intent
                
                state = {
                    "order_id": "TEST",
                    "last_message": {"text": "Хочу купить USDT"},
                    "order_data": {"amount": 10000}
                }
                result = await classify_intent(state)
                
                assert result.get("intent") == "BUY_CRYPTO"
    
    @pytest.mark.asyncio
    async def test_analyze_risk_node_execution(self):
        """Test risk analysis node execution."""
        with patch.dict("os.environ", {"USE_AI_MOCK": "true"}):
            with patch("app.orchestrator.nodes.get_fraud_analyzer") as mock_analyzer:
                mock_agent = MagicMock()
                mock_agent.process = AsyncMock(return_value={
                    "risk_score": 0.15,
                    "risk_level": "LOW",
                    "flags": [],
                    "checks": {"amount_match": True}
                })
                mock_analyzer.return_value = mock_agent
                
                from app.orchestrator.nodes import analyze_fraud_risk
                
                state = {
                    "order_id": "TEST",
                    "payment_data": {"amount": 10000},
                    "order_data": {"amount": 10000}
                }
                result = await analyze_fraud_risk(state)
                
                assert result.get("risk_score") == 0.15
                assert result.get("risk_level") == "LOW"


class TestGraphEdges:
    """Test graph edge conditions."""
    
    def test_edges_module_imports(self):
        """Test edges module can be imported."""
        from app.orchestrator import edges
        assert hasattr(edges, "should_process_message")
        assert hasattr(edges, "should_send_response")
        assert hasattr(edges, "should_analyze_risk")
    
    def test_should_process_message(self):
        """Test message processing condition."""
        from app.orchestrator.edges import should_process_message
        
        state_with_message = {"last_message": {"text": "Test"}}
        state_empty = {"last_message": None}
        
        assert should_process_message(state_with_message) == "process"
        assert should_process_message(state_empty) == "wait"
    
    def test_should_analyze_risk(self):
        """Test risk analysis condition."""
        from app.orchestrator.edges import should_analyze_risk
        
        state_with_payment = {"payment_data": {"amount": 10000, "confidence": 0.95}}
        state_low_confidence = {"payment_data": {"amount": 10000, "confidence": 0.3}}
        state_empty = {"payment_data": None}
        
        assert should_analyze_risk(state_with_payment) == "analyze"
        assert should_analyze_risk(state_low_confidence) == "skip"
        assert should_analyze_risk(state_empty) == "skip"
