"""FastAPI server with WebSocket support for P2P automation UI."""
import logging
import asyncio
from typing import Dict, Set
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from starlette.middleware.cors import CORSMiddleware

from models import StartMonitorRequest, ApprovalRequest, StateResponse
from bybit_client import bybit_client
from app.orchestrator.graph import p2p_graph
from app.orchestrator.state import P2PAutomationState
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to WebSocket: {e}")
                disconnected.add(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()

# Store active runs
active_runs: Dict[str, dict] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    logger.info("Starting P2P Automation Server...")
    config.validate_config()
    yield
    logger.info("Shutting down P2P Automation Server...")

# Create FastAPI app
app = FastAPI(
    title="Bybit P2P Automation",
    description="Human-in-the-loop P2P trading automation",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Serve the main UI."""
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/api/ads")
async def get_ads():
    """Get list of P2P advertisements."""
    try:
        ads = bybit_client.get_ads_list()
        return {"success": True, "data": [ad.model_dump() for ad in ads]}
    except Exception as e:
        logger.error(f"Error fetching ads: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chat/{order_id}")
async def get_chat(order_id: str):
    """Get chat messages for an order."""
    try:
        messages = bybit_client.get_chat_messages(order_id)
        return {"success": True, "data": [msg.model_dump() for msg in messages]}
    except Exception as e:
        logger.error(f"Error fetching chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/balance")
async def get_balance():
    """Get account balance."""
    try:
        balance = bybit_client.get_balance()
        return {"success": True, "data": [b.model_dump() for b in balance]}
    except Exception as e:
        logger.error(f"Error fetching balance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/payment_methods")
async def get_payment_methods():
    """Get available payment methods."""
    try:
        methods = bybit_client.get_payment_methods()
        return {"success": True, "data": methods}
    except Exception as e:
        logger.error(f"Error fetching payment methods: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/order/{order_id}")
async def get_order_details(order_id: str):
    """Get order details."""
    try:
        details = bybit_client.get_order_details(order_id)
        if details:
            return {"success": True, "data": details}
        raise HTTPException(status_code=404, detail="Order not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching order details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/order/{order_id}/cancel")
async def cancel_order(order_id: str):
    """Cancel an order."""
    try:
        success = bybit_client.cancel_order(order_id)
        return {"success": success, "message": "Order cancelled" if success else "Failed to cancel"}
    except Exception as e:
        logger.error(f"Error cancelling order: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/order/{order_id}/confirm_payment")
async def confirm_payment(order_id: str):
    """Confirm payment for an order."""
    try:
        success = bybit_client.confirm_payment(order_id)
        return {"success": success, "message": "Payment confirmed" if success else "Failed to confirm"}
    except Exception as e:
        logger.error(f"Error confirming payment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/trade_history")
async def get_trade_history():
    """Get trade history."""
    try:
        history = bybit_client.get_trade_history()
        return {"success": True, "data": history}
    except Exception as e:
        logger.error(f"Error fetching trade history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/start_monitor")
async def start_monitor(request: StartMonitorRequest):
    """Start monitoring an order."""
    try:
        order_id = request.order_id
        run_id = f"run_{order_id}_{asyncio.get_event_loop().time()}"
        
        initial_state: P2PAutomationState = {
            "order_id": order_id,
            "run_id": run_id,
            "messages": [],
            "response_approval_required": False,
            "risk_approval_required": False
        }
        
        config_dict = {"configurable": {"thread_id": run_id}}
        
        asyncio.create_task(run_graph_async(run_id, initial_state, config_dict))
        
        active_runs[run_id] = {
            "order_id": order_id,
            "status": "running",
            "state": initial_state
        }
        
        await manager.broadcast({
            "type": "monitor_started",
            "run_id": run_id,
            "order_id": order_id
        })
        
        return {"success": True, "run_id": run_id, "order_id": order_id}
    except Exception as e:
        logger.error(f"Error starting monitor: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def run_graph_async(run_id: str, initial_state: P2PAutomationState, config_dict: dict):
    """Run graph asynchronously and broadcast state updates."""
    try:
        result = None
        for event in p2p_graph.stream(initial_state, config_dict):
            logger.info(f"Graph event: {event}")
            
            if isinstance(event, dict):
                for node_name, node_state in event.items():
                    if isinstance(node_state, dict):
                        result = node_state
                    elif isinstance(node_state, tuple):
                        result = node_state[0] if node_state else {}
                    else:
                        result = {}
                    
                    if run_id in active_runs:
                        active_runs[run_id]["state"] = result
                        waiting_approval = result.get("response_approval_required") or result.get("risk_approval_required")
                        active_runs[run_id]["status"] = "waiting_approval" if waiting_approval else "running"
                    
                    await manager.broadcast({
                        "type": "state_update",
                        "run_id": run_id,
                        "node": node_name,
                        "state": {
                            "order_id": result.get("order_id") if isinstance(result, dict) else None,
                            "intent": result.get("intent") if isinstance(result, dict) else None,
                            "intent_confidence": result.get("intent_confidence") if isinstance(result, dict) else None,
                            "proposed_response": result.get("proposed_response") if isinstance(result, dict) else None,
                            "response_approval_required": result.get("response_approval_required", False) if isinstance(result, dict) else False,
                            "risk_approval_required": result.get("risk_approval_required", False) if isinstance(result, dict) else False,
                            "risk_score": result.get("risk_score") if isinstance(result, dict) else None,
                            "risk_level": result.get("risk_level") if isinstance(result, dict) else None,
                            "current_step": result.get("current_step") if isinstance(result, dict) else None,
                            "error": result.get("error") if isinstance(result, dict) else None
                        }
                    })
        
        if run_id in active_runs:
            active_runs[run_id]["status"] = "completed"
            await manager.broadcast({
                "type": "monitor_completed",
                "run_id": run_id
            })
            
    except Exception as e:
        logger.error(f"Error in graph execution: {e}", exc_info=True)
        if run_id in active_runs:
            active_runs[run_id]["status"] = "error"
            active_runs[run_id]["error"] = str(e)
        await manager.broadcast({
            "type": "error",
            "run_id": run_id,
            "error": str(e)
        })

@app.post("/api/approve/{run_id}")
async def approve_action(run_id: str, request: ApprovalRequest):
    """Approve or reject a pending action."""
    try:
        if run_id not in active_runs:
            raise HTTPException(status_code=404, detail="Run not found")
        
        run_info = active_runs[run_id]
        current_state = run_info["state"]
        
        if current_state.get("response_approval_required"):
            current_state["response_approved"] = request.approved
            current_state["response_approval_required"] = False
        elif current_state.get("risk_approval_required"):
            current_state["risk_approved"] = request.approved
            current_state["risk_approval_required"] = False
        
        if request.user_input:
            current_state["proposed_response"] = request.user_input
        
        config_dict = {"configurable": {"thread_id": run_id}}
        asyncio.create_task(run_graph_async(run_id, current_state, config_dict))
        
        await manager.broadcast({
            "type": "approval_submitted",
            "run_id": run_id,
            "approved": request.approved
        })
        
        return {"success": True, "run_id": run_id, "approved": request.approved}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving action: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/runs")
async def get_runs():
    """Get all active runs."""
    return {"success": True, "data": active_runs}

@app.get("/api/run/{run_id}")
async def get_run(run_id: str):
    """Get specific run details."""
    if run_id not in active_runs:
        raise HTTPException(status_code=404, detail="Run not found")
    return {"success": True, "data": active_runs[run_id]}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and receive any client messages
            data = await websocket.receive_text()
            logger.info(f"Received from client: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)
