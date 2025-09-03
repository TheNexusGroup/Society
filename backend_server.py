#!/usr/bin/env python3
"""
Society Simulation Backend Server
Headless simulation server with WebSocket API for real-time monitoring
"""

import asyncio
import json
import time
import threading
from typing import Dict, List, Optional, Set
from pathlib import Path

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Simulation imports
from src.simulation.world.world import World
from src.simulation.model_manager import ModelManager
from src.simulation.speed_optimizer import SpeedOptimizer, SpeedMode
from src.data.metrics import MetricsCollector
import pygame

# Initialize FastAPI
app = FastAPI(
    title="Society Simulation API",
    description="Headless backend for agent-based society simulation",
    version="2.0.0"
)

# CORS middleware for web client
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global simulation state
class SimulationState:
    def __init__(self):
        self.world: Optional[World] = None
        self.model_manager: Optional[ModelManager] = None
        self.speed_optimizer: Optional[SpeedOptimizer] = None
        self.is_running: bool = False
        self.is_paused: bool = False
        self.current_iteration: int = 0
        self.connected_clients: Set[WebSocket] = set()
        self.simulation_thread: Optional[threading.Thread] = None
        self.metrics: Dict = {}
        
    def initialize(self):
        """Initialize simulation components"""
        # Initialize pygame in headless mode
        pygame.init()
        pygame.display.set_mode((1, 1))  # Minimal display
        
        self.model_manager = ModelManager("models")
        self.speed_optimizer = SpeedOptimizer()
        self.world = World(1200, 800)

# Global simulation state
sim_state = SimulationState()

# Pydantic models for API
class ModelConfig(BaseModel):
    name: str
    description: str
    config: Dict

class SimulationCommand(BaseModel):
    action: str  # start, pause, stop, reset
    model_name: Optional[str] = None
    speed_mode: Optional[str] = None

class SpeedChangeRequest(BaseModel):
    speed_mode: str  # normal, fast, faster, fastest

# Initialize simulation on startup
@app.on_event("startup")
async def startup_event():
    """Initialize simulation state"""
    sim_state.initialize()
    print("🚀 Society Simulation Backend Started")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    sim_state.is_running = False
    if sim_state.simulation_thread:
        sim_state.simulation_thread.join(timeout=5.0)
    print("🛑 Society Simulation Backend Stopped")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "simulation_running": sim_state.is_running,
        "connected_clients": len(sim_state.connected_clients),
        "current_iteration": sim_state.current_iteration
    }

# Model management endpoints
@app.get("/api/models")
async def list_models():
    """Get list of available models"""
    if not sim_state.model_manager:
        raise HTTPException(status_code=500, detail="Model manager not initialized")
    
    models = sim_state.model_manager.list_models()
    return {"models": models}

@app.post("/api/models")
async def create_model(model_config: ModelConfig):
    """Create a new model"""
    if not sim_state.model_manager:
        raise HTTPException(status_code=500, detail="Model manager not initialized")
    
    model_name = sim_state.model_manager.create_model(
        model_config.name,
        model_config.description,
        model_config.config
    )
    
    return {"model_name": model_name, "status": "created"}

@app.get("/api/models/{model_name}")
async def get_model_info(model_name: str):
    """Get detailed model information"""
    if not sim_state.model_manager:
        raise HTTPException(status_code=500, detail="Model manager not initialized")
    
    info = sim_state.model_manager.get_model_info(model_name)
    if not info:
        raise HTTPException(status_code=404, detail="Model not found")
    
    return info

@app.delete("/api/models/{model_name}")
async def delete_model(model_name: str):
    """Delete a model"""
    if not sim_state.model_manager:
        raise HTTPException(status_code=500, detail="Model manager not initialized")
    
    success = sim_state.model_manager.delete_model(model_name)
    if not success:
        raise HTTPException(status_code=404, detail="Model not found")
    
    return {"status": "deleted"}

# Simulation control endpoints
@app.post("/api/simulation/control")
async def control_simulation(command: SimulationCommand, background_tasks: BackgroundTasks):
    """Control simulation (start/pause/stop/reset)"""
    if command.action == "start":
        if sim_state.is_running:
            return {"status": "already_running"}
        
        if command.model_name:
            sim_state.model_manager.load_model(command.model_name)
        
        if command.speed_mode:
            speed_mode = SpeedMode[command.speed_mode.upper()]
            sim_state.speed_optimizer.set_speed_mode(speed_mode)
        
        background_tasks.add_task(start_simulation_background)
        return {"status": "starting"}
    
    elif command.action == "pause":
        sim_state.is_paused = not sim_state.is_paused
        return {"status": "paused" if sim_state.is_paused else "resumed"}
    
    elif command.action == "stop":
        sim_state.is_running = False
        return {"status": "stopping"}
    
    elif command.action == "reset":
        sim_state.is_running = False
        if sim_state.world:
            sim_state.world.reset()
        sim_state.current_iteration = 0
        return {"status": "reset"}
    
    else:
        raise HTTPException(status_code=400, detail="Invalid action")

@app.post("/api/simulation/speed")
async def change_speed(speed_request: SpeedChangeRequest):
    """Change simulation speed"""
    if not sim_state.speed_optimizer:
        raise HTTPException(status_code=500, detail="Speed optimizer not initialized")
    
    try:
        speed_mode = SpeedMode[speed_request.speed_mode.upper()]
        sim_state.speed_optimizer.set_speed_mode(speed_mode)
        
        # Broadcast speed change to connected clients
        await broadcast_to_clients({
            "type": "speed_change",
            "speed_mode": speed_mode.name,
            "multiplier": speed_mode.value
        })
        
        return {"status": "speed_changed", "new_speed": speed_mode.name}
    except KeyError:
        raise HTTPException(status_code=400, detail="Invalid speed mode")

@app.get("/api/simulation/status")
async def get_simulation_status():
    """Get current simulation status"""
    performance_metrics = {}
    if sim_state.speed_optimizer:
        performance_metrics = sim_state.speed_optimizer.get_performance_metrics()
    
    return {
        "is_running": sim_state.is_running,
        "is_paused": sim_state.is_paused,
        "current_iteration": sim_state.current_iteration,
        "current_model": sim_state.model_manager.current_model if sim_state.model_manager else None,
        "speed_mode": sim_state.speed_optimizer.current_speed.name if sim_state.speed_optimizer else "NORMAL",
        "connected_clients": len(sim_state.connected_clients),
        "performance": performance_metrics
    }

# Data endpoints
@app.get("/api/simulation/metrics")
async def get_simulation_metrics():
    """Get current simulation metrics"""
    return sim_state.metrics

@app.get("/api/simulation/agents")
async def get_agents_data():
    """Get current agents data"""
    if not sim_state.world:
        return {"agents": []}
    
    agents_data = []
    agent_entities = sim_state.world.ecs.get_entities_with_components(["behavior", "transform", "wallet"])
    
    for entity_id in agent_entities[:100]:  # Limit to first 100 for performance
        behavior = sim_state.world.ecs.get_component(entity_id, "behavior")
        transform = sim_state.world.ecs.get_component(entity_id, "transform")
        wallet = sim_state.world.ecs.get_component(entity_id, "wallet")
        
        if behavior and transform and wallet:
            agents_data.append({
                "id": entity_id,
                "position": transform.position,
                "state": behavior.state,
                "energy": wallet.energy,
                "money": wallet.money,
                "food": wallet.food
            })
    
    return {"agents": agents_data, "total_count": len(agent_entities)}

# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time simulation updates"""
    await websocket.accept()
    sim_state.connected_clients.add(websocket)
    
    try:
        while True:
            # Send periodic updates
            if sim_state.is_running:
                update_data = {
                    "type": "simulation_update",
                    "iteration": sim_state.current_iteration,
                    "metrics": sim_state.metrics,
                    "timestamp": time.time()
                }
                await websocket.send_text(json.dumps(update_data))
            
            # Listen for client messages
            try:
                message = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
                client_data = json.loads(message)
                
                # Handle client requests
                if client_data.get("type") == "request_agents":
                    agents_response = await get_agents_data()
                    agents_response["type"] = "agents_data"
                    await websocket.send_text(json.dumps(agents_response))
                
            except asyncio.TimeoutError:
                continue  # No message received, continue loop
            
    except WebSocketDisconnect:
        sim_state.connected_clients.discard(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        sim_state.connected_clients.discard(websocket)

# Static file serving for web client
if Path("web_client/build").exists():
    app.mount("/static", StaticFiles(directory="web_client/build/static"), name="static")

@app.get("/")
async def serve_web_client():
    """Serve the web client"""
    client_path = Path("web_client/build/index.html")
    if client_path.exists():
        return FileResponse(client_path)
    else:
        return HTMLResponse("""
        <html>
            <head><title>Society Simulation</title></head>
            <body>
                <h1>Society Simulation Backend</h1>
                <p>Backend is running. Web client not built yet.</p>
                <p>API available at: <a href="/docs">/docs</a></p>
            </body>
        </html>
        """)

# Background simulation function
async def start_simulation_background():
    """Start simulation in background thread"""
    if sim_state.is_running:
        return
    
    sim_state.is_running = True
    sim_state.simulation_thread = threading.Thread(target=simulation_loop, daemon=True)
    sim_state.simulation_thread.start()

def simulation_loop():
    """Main simulation loop running in background thread"""
    print("🎯 Starting simulation loop")
    
    last_time = time.time()
    frame_count = 0
    
    while sim_state.is_running:
        if sim_state.is_paused:
            time.sleep(0.1)
            continue
        
        frame_start = time.time()
        dt = frame_start - last_time
        last_time = frame_start
        
        try:
            # Update world with speed optimization
            if sim_state.world and sim_state.speed_optimizer:
                sim_state.speed_optimizer.optimize_world_update(sim_state.world, dt)
                
                # Update iteration counter
                sim_state.current_iteration += 1
                
                # Collect metrics every 60 frames
                if frame_count % 60 == 0:
                    sim_state.metrics = collect_simulation_metrics()
                
                # Auto-save checkpoints every 1000 iterations
                if sim_state.current_iteration % 1000 == 0:
                    if sim_state.model_manager:
                        sim_state.model_manager.increment_iteration(1000)
                        checkpoint_name = sim_state.model_manager.save_checkpoint(
                            sim_state.world, 
                            auto_save=True
                        )
                        print(f"💾 Auto-saved checkpoint: {checkpoint_name}")
                
                # Update speed optimizer timing
                sim_state.speed_optimizer.update_frame_timing(frame_start)
                
                frame_count += 1
        
        except Exception as e:
            print(f"❌ Simulation error: {e}")
            time.sleep(1.0)  # Prevent rapid error loop

def collect_simulation_metrics() -> Dict:
    """Collect current simulation metrics"""
    if not sim_state.world:
        return {}
    
    agents = sim_state.world.ecs.get_entities_with_components(["behavior", "wallet"])
    
    # Basic metrics
    total_agents = len(agents)
    alive_agents = 0
    dead_agents = 0
    total_wealth = 0.0
    total_food = 0.0
    total_energy = 0.0
    
    state_counts = {}
    
    for entity_id in agents:
        behavior = sim_state.world.ecs.get_component(entity_id, "behavior")
        wallet = sim_state.world.ecs.get_component(entity_id, "wallet")
        
        if not behavior or not wallet:
            continue
        
        # Count states
        state = behavior.state
        state_counts[state] = state_counts.get(state, 0) + 1
        
        if state == "dead":
            dead_agents += 1
        else:
            alive_agents += 1
            total_wealth += wallet.money
            total_food += wallet.food
            total_energy += wallet.energy
    
    # Performance metrics
    performance = {}
    if sim_state.speed_optimizer:
        performance = sim_state.speed_optimizer.get_performance_metrics()
    
    return {
        "population": {
            "total": total_agents,
            "alive": alive_agents,
            "dead": dead_agents
        },
        "economy": {
            "total_wealth": total_wealth,
            "avg_wealth": total_wealth / alive_agents if alive_agents > 0 else 0,
            "total_food": total_food,
            "avg_food": total_food / alive_agents if alive_agents > 0 else 0
        },
        "energy": {
            "total_energy": total_energy,
            "avg_energy": total_energy / alive_agents if alive_agents > 0 else 0
        },
        "behaviors": state_counts,
        "performance": performance,
        "iteration": sim_state.current_iteration
    }

async def broadcast_to_clients(data: Dict):
    """Broadcast data to all connected WebSocket clients"""
    if not sim_state.connected_clients:
        return
    
    message = json.dumps(data)
    disconnected_clients = set()
    
    for client in sim_state.connected_clients:
        try:
            await client.send_text(message)
        except:
            disconnected_clients.add(client)
    
    # Remove disconnected clients
    sim_state.connected_clients -= disconnected_clients

if __name__ == "__main__":
    uvicorn.run(
        "backend_server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        workers=1,
        log_level="info"
    )