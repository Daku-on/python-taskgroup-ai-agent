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
from ..services.interview_services import (
    InterviewOrchestratorService,
    GoogleCalendarService,
    GmailService,
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


class InterviewRequest(BaseModel):
    """面接スケジューリングリクエスト。"""
    
    candidate_name: str
    candidate_email: str
    interviewer_names: List[str]
    interviewer_emails: List[str]
    duration_minutes: int = 60
    preferred_dates: Optional[List[str]] = None
    auto_select: bool = True


class InterviewResponse(BaseModel):
    """面接スケジューリングレスポンス。"""
    
    request_id: str
    status: str
    scheduled_time: Optional[str] = None
    meet_link: Optional[str] = None
    calendar_event_id: Optional[str] = None
    email_message_id: Optional[str] = None
    available_slots: Optional[List[Dict]] = None
    error: Optional[str] = None


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
    
    # Interview services
    interview_service = InterviewOrchestratorService(
        name="interview-orchestrator-service"
    )
    
    calendar_service = GoogleCalendarService(
        name="google-calendar-service"
    )
    
    gmail_service = GmailService(
        name="gmail-service"
    )
    
    await registry.register_service(llm_service)
    await registry.register_service(db_service)
    await registry.register_service(rag_service)
    await registry.register_service(interview_service)
    await registry.register_service(calendar_service)
    await registry.register_service(gmail_service)
    
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
        "rag": "rag-agent-service",
        "interview": "interview-orchestrator-service",
        "calendar": "google-calendar-service",
        "gmail": "gmail-service"
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


@app.post("/interviews/schedule", response_model=InterviewResponse)
async def schedule_interview(request: InterviewRequest):
    """面接を自動スケジューリング。"""
    if not registry:
        raise HTTPException(status_code=503, detail="Service registry not available")
    
    service = registry._services.get("interview-orchestrator-service")
    if not service:
        raise HTTPException(status_code=404, detail="Interview service not found")
    
    try:
        # 日付文字列をdatetimeに変換
        preferred_dates = None
        if request.preferred_dates:
            from datetime import datetime
            preferred_dates = [
                datetime.fromisoformat(date) for date in request.preferred_dates
            ]
        
        # 面接データを準備
        interview_data = {
            "candidate_name": request.candidate_name,
            "candidate_email": request.candidate_email,
            "interviewer_names": request.interviewer_names,
            "interviewer_emails": request.interviewer_emails,
            "duration_minutes": request.duration_minutes,
            "preferred_dates": preferred_dates
        }
        
        # 面接スケジューリング実行
        result = await service.process_single_interview(interview_data)
        
        # WebSocket経由で進行状況を通知
        await manager.broadcast(f"Interview scheduled for {request.candidate_name}")
        
        return InterviewResponse(
            request_id=result.get("request_id", f"interview_{request.candidate_name}"),
            status=result["status"],
            scheduled_time=result.get("scheduled_time"),
            meet_link=result.get("meet_link"),
            calendar_event_id=result.get("calendar_event_id"),
            email_message_id=result.get("email_message_id"),
            error=result.get("error")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/interviews/available-slots")
async def get_available_slots(
    candidate_email: str,
    interviewer_emails: str,  # カンマ区切り
    duration_minutes: int = 60,
    days_ahead: int = 7
):
    """利用可能な面接時間枠を取得。"""
    if not registry:
        raise HTTPException(status_code=503, detail="Service registry not available")
    
    service = registry._services.get("google-calendar-service")
    if not service:
        raise HTTPException(status_code=404, detail="Calendar service not found")
    
    try:
        from datetime import datetime, timedelta
        
        # 希望日程を生成（明日から指定日数）
        tomorrow = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        preferred_dates = []
        for i in range(days_ahead):
            date = tomorrow + timedelta(days=i)
            if date.weekday() < 5:  # 平日のみ
                preferred_dates.append(date)
        
        # カレンダーサービスで空き時間検索
        from ..agent.google_calendar_agent import find_interview_slots
        
        interviewer_list = [email.strip() for email in interviewer_emails.split(',')]
        
        slots = await find_interview_slots(
            candidate_email=candidate_email,
            interviewer_emails=interviewer_list,
            duration_minutes=duration_minutes,
            preferred_dates=preferred_dates
        )
        
        return {
            "available_slots": [
                {
                    "start": slot.start.isoformat(),
                    "end": slot.end.isoformat(),
                    "attendees": slot.attendees
                }
                for slot in slots
            ]
        }
        
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