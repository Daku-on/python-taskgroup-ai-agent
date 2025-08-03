"""FastAPI アプリケーションのメインファイル。"""

import asyncio
import os
from contextlib import asynccontextmanager
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ..services.orchestrator import OrchestratorService
from ..services.registry import ServiceRegistry
from ..services.agent_services import (
    LLMAgentService,
    DatabaseService,
    RAGAgentService,
)
from ..agent.base import Task


# WebSocket接続管理
class ConnectionManager:
    """WebSocket接続を管理するクラス。"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """WebSocket接続を追加。"""
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        """WebSocket接続を削除。"""
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """特定の接続にメッセージ送信。"""
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        """全接続にメッセージをブロードキャスト。"""
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                # 切断された接続は無視
                pass


# Pydanticモデル
class TaskRequest(BaseModel):
    """タスク実行リクエスト。"""
    
    name: str
    agent_type: str  # "llm", "database", "smart_knowledge"
    data: Dict
    

class TaskResponse(BaseModel):
    """タスク実行レスポンス。"""
    
    task_id: str
    name: str
    status: str
    result: Optional[str] = None
    error: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None


class ServiceStatus(BaseModel):
    """サービス状態。"""
    
    name: str
    status: str
    health: bool
    metrics: Dict


class WorkflowRequest(BaseModel):
    """ワークフロー実行リクエスト。"""
    
    name: str
    steps: List[Dict]


# グローバル変数
registry: Optional[ServiceRegistry] = None
orchestrator: Optional[OrchestratorService] = None
manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションライフサイクル管理。"""
    global registry, orchestrator
    
    # 起動時処理
    registry = ServiceRegistry()
    await registry.start()
    
    # サービス登録
    llm_service = LLMAgentService(
        name="llm-agent-service"
    )
    
    db_service = DatabaseService(
        name="database-service"
    )
    
    rag_service = RAGAgentService(
        name="rag-agent-service"
    )
    
    await registry.register_service(llm_service)
    await registry.register_service(db_service)
    await registry.register_service(rag_service)
    
    # オーケストレーター作成
    orchestrator = OrchestratorService(registry)
    await orchestrator.start()
    
    yield
    
    # 終了時処理
    if orchestrator:
        await orchestrator.stop()
    if registry:
        await registry.stop()


# FastAPIアプリケーション作成
app = FastAPI(
    title="Python TaskGroup AI Agent API",
    description="TaskGroupを使用したAIエージェント管理API",
    version="0.1.0",
    lifespan=lifespan
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Vite, Create React App
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# エンドポイント
@app.get("/")
async def root():
    """ルートエンドポイント。"""
    return {"message": "Python TaskGroup AI Agent API"}


@app.get("/health")
async def health_check():
    """ヘルスチェック。"""
    return {"status": "healthy", "registry": registry is not None}


@app.get("/services", response_model=List[ServiceStatus])
async def get_services():
    """登録されているサービス一覧を取得。"""
    if not registry:
        raise HTTPException(status_code=503, detail="Service registry not available")
    
    services = []
    for service_name, service in registry._services.items():
        health = await service.health_check()
        services.append(ServiceStatus(
            name=service_name,
            status=service._status,
            health=health,
            metrics=service._metrics
        ))
    
    return services


@app.post("/tasks/execute", response_model=TaskResponse)
async def execute_task(request: TaskRequest):
    """単一タスクを実行。"""
    if not registry:
        raise HTTPException(status_code=503, detail="Service registry not available")
    
    # サービス名マッピング
    service_mapping = {
        "llm": "llm-agent-service",
        "database": "database-service", 
        "rag": "rag-agent-service"
    }
    
    service_name = service_mapping.get(request.agent_type)
    if not service_name:
        raise HTTPException(status_code=400, detail="Invalid agent type")
    
    service = registry._services.get(service_name)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    # タスク作成
    task_id = f"task_{asyncio.get_event_loop().time()}"
    task = Task(id=task_id, name=request.name, data=request.data)
    
    # タスク実行
    try:
        result_task = await service.process_single_task(task)
        
        # WebSocket経由で進行状況を通知
        await manager.broadcast(f"Task {task_id} completed")
        
        return TaskResponse(
            task_id=result_task.id,
            name=result_task.name,
            status="completed" if not result_task.error else "failed",
            result=str(result_task.result) if result_task.result else None,
            error=str(result_task.error) if result_task.error else None,
            created_at=result_task.created_at.isoformat(),
            completed_at=result_task.completed_at.isoformat() if result_task.completed_at else None
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/workflows/execute")
async def execute_workflow(request: WorkflowRequest):
    """ワークフローを実行。"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not available")
    
    try:
        result = await orchestrator.execute_workflow(request.name, request.steps)
        
        # WebSocket経由で進行状況を通知
        await manager.broadcast(f"Workflow {request.name} completed")
        
        return {"workflow_id": request.name, "result": result}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket接続エンドポイント（リアルタイム更新用）。"""
    await manager.connect(websocket)
    try:
        while True:
            # 定期的に状態更新を送信
            if registry:
                status_update = {
                    "type": "status_update",
                    "services": len(registry._services),
                    "timestamp": asyncio.get_event_loop().time()
                }
                await manager.send_personal_message(str(status_update), websocket)
            
            await asyncio.sleep(5)  # 5秒間隔で更新
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)