"""FastAPI server with WebSocket support for P2P automation UI."""
import signal
import asyncio
import os
from datetime import datetime
from typing import Dict, Set, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from sqlalchemy import text

from models import (
    StartMonitorRequest, ApprovalRequest, StateResponse,
    CreateAdRequest, UpdateAdRequest, SendMessageRequest, MarkPaidRequest
)
from bybit_client import bybit_client
from app.orchestrator.graph import get_p2p_graph
from app.orchestrator.state import P2PAutomationState
from app.core import (
    setup_logging, get_logger,
    get_current_user, get_admin_user, get_optional_user, get_optional_user_ws,
    SecurityMiddleware, RateLimitMiddleware, rate_limiter,
    SecurityHeadersMiddleware, CORSSecurityMiddleware
)
from app.api.auth import router as auth_router
from app.database.security_models import User
import config

logger = get_logger(__name__)
shutdown_event = asyncio.Event()
DEBUG = os.getenv("DEBUG", "false").lower() == "true"


def signal_handler(sig, frame):
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {sig}, initiating graceful shutdown...")
    shutdown_event.set()


def check_database_connection():
    """Verify database connection on startup (sync)."""
    try:
        from app.database.session import engine
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection verified")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.user_connections: Dict[int, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: Optional[int] = None):
        await websocket.accept()
        self.active_connections.add(websocket)
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        for user_id, connections in self.user_connections.items():
            connections.discard(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict, user_id: Optional[int] = None):
        """Broadcast message to all clients or specific user."""
        disconnected = set()
        connections = self.user_connections.get(user_id, self.active_connections) if user_id else self.active_connections
        
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to WebSocket: {e}")
                disconnected.add(connection)
        
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()

active_runs: Dict[str, dict] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan with startup/shutdown handlers."""
    setup_logging(log_level="DEBUG" if DEBUG else "INFO", log_file="logs/app.log")
    logger.info("Starting P2P Automation Server...")
    
    try:
        config.validate_config()
        logger.info("Configuration validated")
    except Exception as e:
        logger.error(f"Configuration error: {e}")
        raise
    
    db_ok = check_database_connection()
    if not db_ok:
        logger.warning("Database check failed - continuing anyway")
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        from app.database import init_db
        init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.warning(f"Database init warning: {e}")
    
    await rate_limiter.init_redis()
    logger.info("Rate limiter initialized")
    
    yield
    
    logger.info("Initiating graceful shutdown...")
    await rate_limiter.close()
    try:
        await asyncio.wait_for(shutdown_event.wait(), timeout=10.0)
    except asyncio.TimeoutError:
        logger.warning("Shutdown timeout - forcing exit")
    logger.info("Shutdown complete")

app = FastAPI(
    title="Bybit P2P Automation",
    description="Human-in-the-loop P2P trading automation",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(SecurityHeadersMiddleware)

allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",")
app.add_middleware(CORSSecurityMiddleware, allowed_origins=allowed_origins)

app.add_middleware(RateLimitMiddleware, rate_limiter=rate_limiter)

app.add_middleware(SecurityMiddleware)

app.include_router(auth_router)

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Serve the main UI."""
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/api/ads")
async def get_ads(current_user: User = Depends(get_current_user)):
    """Get list of P2P advertisements (requires authentication)."""
    try:
        ads = bybit_client.get_ads_list()
        return {"success": True, "data": [ad.model_dump() for ad in ads]}
    except Exception as e:
        logger.error(f"Error fetching ads: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ads")
async def create_ad(request: CreateAdRequest, current_user: User = Depends(get_current_user)):
    """Create a new P2P advertisement (requires authentication)."""
    try:
        ad_id = bybit_client.create_ad(
            side=request.side,
            currency=request.currency,
            crypto=request.crypto,
            price=request.price,
            min_amount=request.min_amount,
            max_amount=request.max_amount,
            payment_methods=request.payment_methods
        )
        if ad_id:
            return {"success": True, "ad_id": ad_id}
        raise HTTPException(status_code=400, detail="Failed to create ad")
    except Exception as e:
        logger.error(f"Error creating ad: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ads/online")
async def get_online_ads(
    token: str = "USDT",
    currency: str = "RUB",
    side: str = "SELL",
    current_user: User = Depends(get_current_user)
):
    """Get public online advertisements (requires authentication)."""
    try:
        ads = bybit_client.get_online_ads(token=token, currency=currency, side="1" if side == "SELL" else "0")
        return {"success": True, "data": ads}
    except Exception as e:
        logger.error(f"Error fetching online ads: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ads/{ad_id}")
async def get_ad_details(ad_id: str, current_user: User = Depends(get_current_user)):
    """Get advertisement details (requires authentication)."""
    try:
        details = bybit_client.get_ad_details(ad_id)
        if details:
            return {"success": True, "data": details}
        raise HTTPException(status_code=404, detail="Ad not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching ad details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/ads/{ad_id}")
async def update_ad(ad_id: str, request: UpdateAdRequest, current_user: User = Depends(get_current_user)):
    """Update an advertisement (requires authentication)."""
    try:
        success = bybit_client.update_ad(
            ad_id=ad_id,
            price=request.price,
            min_amount=request.min_amount,
            max_amount=request.max_amount
        )
        return {"success": success, "message": "Ad updated" if success else "Failed to update"}
    except Exception as e:
        logger.error(f"Error updating ad: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/ads/{ad_id}")
async def delete_ad(ad_id: str, current_user: User = Depends(get_current_user)):
    """Delete an advertisement (requires authentication)."""
    try:
        success = bybit_client.cancel_order(ad_id)
        return {"success": success, "message": "Ad deleted" if success else "Failed to delete"}
    except Exception as e:
        logger.error(f"Error deleting ad: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chat/{order_id}")
async def get_chat(order_id: str, current_user: User = Depends(get_current_user)):
    """Get chat messages for an order (requires authentication)."""
    try:
        messages = bybit_client.get_chat_messages(order_id)
        return {"success": True, "data": [msg.model_dump() for msg in messages]}
    except Exception as e:
        logger.error(f"Error fetching chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/{order_id}/send")
async def send_chat_message(order_id: str, request: SendMessageRequest, current_user: User = Depends(get_current_user)):
    """Send a message in order chat (requires authentication)."""
    try:
        success = bybit_client.send_chat_message(order_id, request.text)
        return {"success": success, "message": "Message sent" if success else "Failed to send"}
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/balance")
async def get_balance(current_user: User = Depends(get_current_user)):
    """Get account balance (requires authentication)."""
    try:
        balance = bybit_client.get_balance()
        return {"success": True, "data": [b.model_dump() for b in balance]}
    except Exception as e:
        logger.error(f"Error fetching balance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/payment_methods")
async def get_payment_methods(current_user: User = Depends(get_current_user)):
    """Get available payment methods (requires authentication)."""
    try:
        methods = bybit_client.get_payment_methods()
        return {"success": True, "data": methods}
    except Exception as e:
        logger.error(f"Error fetching payment methods: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/account")
async def get_account_info(current_user: User = Depends(get_current_user)):
    """Get account information (requires authentication)."""
    try:
        info = bybit_client.get_account_information()
        if info:
            return {"success": True, "data": info}
        raise HTTPException(status_code=404, detail="Account info not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching account info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/counterparty/{order_id}")
async def get_counterparty_info(order_id: str, current_user: User = Depends(get_current_user)):
    """Get counterparty information (requires authentication)."""
    try:
        info = bybit_client.get_counterparty_info(order_id)
        if info:
            return {"success": True, "data": info}
        raise HTTPException(status_code=404, detail="Counterparty not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching counterparty info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/order/{order_id}")
async def get_order_details(order_id: str, current_user: User = Depends(get_current_user)):
    """Get order details (requires authentication)."""
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
async def cancel_order(order_id: str, current_user: User = Depends(get_current_user)):
    """Cancel an order (requires authentication)."""
    try:
        success = bybit_client.cancel_order(order_id)
        return {"success": success, "message": "Order cancelled" if success else "Failed to cancel"}
    except Exception as e:
        logger.error(f"Error cancelling order: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/order/{order_id}/confirm_payment")
async def confirm_payment(order_id: str, current_user: User = Depends(get_current_user)):
    """Confirm payment for an order (requires authentication)."""
    try:
        success = bybit_client.confirm_payment(order_id)
        return {"success": success, "message": "Payment confirmed" if success else "Failed to confirm"}
    except Exception as e:
        logger.error(f"Error confirming payment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/trade_history")
async def get_trade_history(current_user: User = Depends(get_current_user)):
    """Get trade history (requires authentication)."""
    try:
        history = bybit_client.get_trade_history()
        return {"success": True, "data": history}
    except Exception as e:
        logger.error(f"Error fetching trade history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/orders")
async def get_orders(page: int = 1, size: int = 20, current_user: User = Depends(get_current_user)):
    """Get all orders (requires authentication)."""
    try:
        orders = bybit_client.get_orders(page=page, size=size)
        return {"success": True, "data": orders, "page": page, "size": size}
    except Exception as e:
        logger.error(f"Error fetching orders: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/orders/pending")
async def get_pending_orders(page: int = 1, size: int = 20, current_user: User = Depends(get_current_user)):
    """Get pending orders (requires authentication)."""
    try:
        orders = bybit_client.get_pending_orders(page=page, size=size)
        return {"success": True, "data": orders, "page": page, "size": size}
    except Exception as e:
        logger.error(f"Error fetching pending orders: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/order/{order_id}/mark_paid")
async def mark_order_paid(order_id: str, request: MarkPaidRequest, current_user: User = Depends(get_current_user)):
    """Mark order as paid (buyer action, requires authentication)."""
    try:
        success = bybit_client.mark_as_paid(
            order_id=order_id,
            payment_type=request.payment_type,
            payment_id=request.payment_id
        )
        return {"success": success, "message": "Order marked as paid" if success else "Failed"}
    except Exception as e:
        logger.error(f"Error marking order as paid: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/order/{order_id}/release")
async def release_order_assets(order_id: str, current_user: User = Depends(get_current_user)):
    """Release assets to buyer (seller action, requires authentication)."""
    try:
        success = bybit_client.release_assets(order_id)
        return {"success": success, "message": "Assets released" if success else "Failed"}
    except Exception as e:
        logger.error(f"Error releasing assets: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/start_monitor")
async def start_monitor(request: StartMonitorRequest, current_user: User = Depends(get_current_user)):
    """Start monitoring an order (requires authentication)."""
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
        
        asyncio.create_task(run_graph_async(run_id, initial_state, config_dict, current_user.id))
        
        active_runs[run_id] = {
            "order_id": order_id,
            "status": "running",
            "state": initial_state,
            "user_id": current_user.id
        }
        
        await manager.broadcast({
            "type": "monitor_started",
            "run_id": run_id,
            "order_id": order_id
        }, user_id=current_user.id)
        
        return {"success": True, "run_id": run_id, "order_id": order_id}
    except Exception as e:
        logger.error(f"Error starting monitor: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def run_graph_async(run_id: str, initial_state: P2PAutomationState, config_dict: dict, user_id: Optional[int] = None):
    """Run graph asynchronously and broadcast state updates."""
    try:
        graph = await get_p2p_graph()
        result = None
        async for event in graph.astream(initial_state, config_dict):
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
                    }, user_id=user_id)
        
        if run_id in active_runs:
            active_runs[run_id]["status"] = "completed"
            await manager.broadcast({
                "type": "monitor_completed",
                "run_id": run_id
            }, user_id=user_id)
            
    except Exception as e:
        logger.error(f"Error in graph execution: {e}", exc_info=True)
        if run_id in active_runs:
            active_runs[run_id]["status"] = "error"
            active_runs[run_id]["error"] = str(e)
        await manager.broadcast({
            "type": "error",
            "run_id": run_id,
            "error": str(e)
        }, user_id=user_id)

@app.post("/api/approve/{run_id}")
async def approve_action(run_id: str, request: ApprovalRequest, current_user: User = Depends(get_current_user)):
    """Approve or reject a pending action (requires authentication)."""
    try:
        if run_id not in active_runs:
            raise HTTPException(status_code=404, detail="Run not found")
        
        run_info = active_runs[run_id]
        
        if run_info.get("user_id") and run_info["user_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
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
        asyncio.create_task(run_graph_async(run_id, current_state, config_dict, current_user.id))
        
        await manager.broadcast({
            "type": "approval_submitted",
            "run_id": run_id,
            "approved": request.approved
        }, user_id=current_user.id)
        
        return {"success": True, "run_id": run_id, "approved": request.approved}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving action: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/runs")
async def get_runs(current_user: User = Depends(get_current_user)):
    """Get all active runs for current user (requires authentication)."""
    user_runs = {
        run_id: run_info 
        for run_id, run_info in active_runs.items()
        if run_info.get("user_id") == current_user.id
    }
    return {"success": True, "data": user_runs}

@app.get("/api/run/{run_id}")
async def get_run(run_id: str, current_user: User = Depends(get_current_user)):
    """Get specific run details (requires authentication)."""
    if run_id not in active_runs:
        raise HTTPException(status_code=404, detail="Run not found")
    
    run_info = active_runs[run_id]
    if run_info.get("user_id") and run_info["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return {"success": True, "data": run_info}

@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    current_user: Optional[User] = Depends(get_optional_user_ws)
):
    """WebSocket endpoint with optional authentication.

    Token should be passed via query parameter 'token'.
    Example: ws://localhost:8000/ws?token=<jwt_token>
    """
    user_id = current_user.id if current_user else None
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"Received from client: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

@app.get("/health")
async def healthcheck():
    """Health check endpoint for Docker/Kubernetes probes."""
    checks = {
        "status": "healthy",
        "version": "2.1.0",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {}
    }
    
    try:
        from app.database.session import engine
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["components"]["database"] = "ok"
    except Exception as e:
        checks["components"]["database"] = f"error: {str(e)[:50]}"
        checks["status"] = "degraded"
    
    redis_enabled = os.getenv("REDIS_ENABLED", "false").lower() == "true"
    if redis_enabled:
        try:
            import redis
            r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
            r.ping()
            checks["components"]["redis"] = "ok"
        except Exception as e:
            checks["components"]["redis"] = f"error: {str(e)[:50]}"
            checks["status"] = "degraded"
    else:
        checks["components"]["redis"] = "ok (disabled)"
    
    status_code = 200 if checks["status"] == "healthy" else 503
    return JSONResponse(content=checks, status_code=status_code)

@app.get("/health/live")
async def liveness():
    """Kubernetes liveness probe."""
    return {"status": "alive"}

@app.get("/health/ready")
async def readiness():
    """Kubernetes readiness probe."""
    return {"status": "ready"}

@app.post("/shutdown")
async def trigger_shutdown(admin: User = Depends(get_admin_user)):
    """Trigger graceful shutdown (admin only)."""
    os.kill(os.getpid(), signal.SIGTERM)
    return {"status": "shutting down"}
