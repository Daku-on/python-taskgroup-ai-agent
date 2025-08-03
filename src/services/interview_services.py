"""面接スケジューリング用サービス実装。"""

from typing import Any, Optional, List, Dict
import os
from datetime import datetime
from dotenv import load_dotenv

from .base import BaseService, ServiceRequest
from ..agent.base import Task
from ..agent.interview_orchestrator import (
    InterviewOrchestrator,
    InterviewRequest,
    schedule_interview_automatically,
    process_multiple_interviews
)
from ..agent.google_calendar_agent import GoogleCalendarAgent, find_interview_slots
from ..agent.gmail_agent import GmailAgent

load_dotenv()


class InterviewOrchestratorService(BaseService):
    """面接オーケストレーターサービス。"""

    def __init__(
        self,
        name: str = "interview-orchestrator-service",
        **kwargs,
    ):
        super().__init__(
            name=name,
            description="面接日程調整の完全自動化を提供するサービス",
            version="1.0.0",
            tags=["interview", "scheduling", "google", "automation"],
            dependencies=["google-calendar", "gmail"],
            **kwargs,
        )

        self._orchestrator: Optional[InterviewOrchestrator] = None

    async def _on_start(self) -> None:
        """オーケストレーター初期化。"""
        self._orchestrator = InterviewOrchestrator()
        await self._orchestrator.__aenter__()

    async def _on_stop(self) -> None:
        """オーケストレーター終了処理。"""
        if self._orchestrator:
            await self._orchestrator.__aexit__(None, None, None)
            self._orchestrator = None

    async def _health_check(self) -> bool:
        """サービスヘルスチェック。"""
        if not self._orchestrator:
            return False

        try:
            # 簡単なテスト（Google認証確認）
            test_task = Task(
                id="health_check",
                name="ヘルスチェック",
                data={
                    "operation": "find_available_slots",
                    "request": {
                        "request_id": "health_check",
                        "candidate_name": "Test User",
                        "candidate_email": "test@example.com",
                        "interviewer_names": ["Test Interviewer"],
                        "interviewer_emails": ["interviewer@example.com"],
                        "duration_minutes": 30,
                        "preferred_dates": [datetime.now()]
                    }
                }
            )

            result = await self._orchestrator.run_single_task(test_task)
            return result.error is None

        except Exception:
            return False

    async def _process_request(self, request: ServiceRequest) -> Any:
        """面接スケジューリングリクエスト処理。"""
        if not self._orchestrator:
            raise RuntimeError("Interview orchestrator is not initialized")

        operation = request.operation
        data = request.data

        if operation == "schedule_automatic":
            # 完全自動スケジューリング
            interview_request = InterviewRequest(**data["request"])
            auto_select = data.get("auto_select", True)

            task = Task(
                id=request.request_id,
                name="自動面接スケジューリング",
                data={
                    "operation": "schedule_complete_interview",
                    "request": {
                        "request_id": interview_request.request_id,
                        "candidate_name": interview_request.candidate_name,
                        "candidate_email": interview_request.candidate_email,
                        "interviewer_names": interview_request.interviewer_names,
                        "interviewer_emails": interview_request.interviewer_emails,
                        "duration_minutes": interview_request.duration_minutes,
                        "preferred_dates": interview_request.preferred_dates
                    },
                    "auto_select": auto_select
                }
            )

            result = await self._orchestrator.run_single_task(task)

            if result.error:
                raise Exception(f"Interview scheduling failed: {result.error}")

            return {
                "request_id": result.result.request_id,
                "status": result.result.status.value,
                "scheduled_time": result.result.scheduled_time.isoformat() if result.result.scheduled_time else None,
                "meet_link": result.result.meet_link,
                "calendar_event_id": result.result.calendar_event_id,
                "email_message_id": result.result.email_message_id,
                "available_slots": [
                    {
                        "start": slot.start.isoformat(),
                        "end": slot.end.isoformat(),
                        "attendees": slot.attendees
                    }
                    for slot in (result.result.available_slots or [])
                ] if result.result.available_slots else None
            }

        elif operation == "find_slots":
            # 空き時間検索のみ
            interview_request = InterviewRequest(**data["request"])

            task = Task(
                id=request.request_id,
                name="空き時間検索",
                data={
                    "operation": "find_available_slots",
                    "request": {
                        "request_id": interview_request.request_id,
                        "candidate_name": interview_request.candidate_name,
                        "candidate_email": interview_request.candidate_email,
                        "interviewer_names": interview_request.interviewer_names,
                        "interviewer_emails": interview_request.interviewer_emails,
                        "duration_minutes": interview_request.duration_minutes,
                        "preferred_dates": interview_request.preferred_dates
                    }
                }
            )

            result = await self._orchestrator.run_single_task(task)

            if result.error:
                raise Exception(f"Slot finding failed: {result.error}")

            return {
                "available_slots": [
                    {
                        "start": slot.start.isoformat(),
                        "end": slot.end.isoformat(),
                        "attendees": slot.attendees
                    }
                    for slot in result.result
                ]
            }

        elif operation == "confirm_slot":
            # 指定スロットで確定
            interview_request = InterviewRequest(**data["request"])
            selected_slot = data["selected_slot"]

            task = Task(
                id=request.request_id,
                name="面接確定",
                data={
                    "operation": "confirm_interview_slot",
                    "request": {
                        "request_id": interview_request.request_id,
                        "candidate_name": interview_request.candidate_name,
                        "candidate_email": interview_request.candidate_email,
                        "interviewer_names": interview_request.interviewer_names,
                        "interviewer_emails": interview_request.interviewer_emails,
                        "duration_minutes": interview_request.duration_minutes
                    },
                    "selected_slot": selected_slot
                }
            )

            result = await self._orchestrator.run_single_task(task)

            if result.error:
                raise Exception(f"Interview confirmation failed: {result.error}")

            return {
                "request_id": result.result.request_id,
                "status": result.result.status.value,
                "scheduled_time": result.result.scheduled_time.isoformat(),
                "meet_link": result.result.meet_link,
                "calendar_event_id": result.result.calendar_event_id,
                "email_message_id": result.result.email_message_id
            }

        elif operation == "batch_schedule":
            # バッチ処理
            interview_requests = [InterviewRequest(**req) for req in data["requests"]]

            tasks = []
            for i, req in enumerate(interview_requests):
                task = Task(
                    id=f"batch_{i}",
                    name=f"バッチ面接_{req.candidate_name}",
                    data={
                        "operation": "schedule_complete_interview",
                        "request": {
                            "request_id": req.request_id,
                            "candidate_name": req.candidate_name,
                            "candidate_email": req.candidate_email,
                            "interviewer_names": req.interviewer_names,
                            "interviewer_emails": req.interviewer_emails,
                            "duration_minutes": req.duration_minutes,
                            "preferred_dates": req.preferred_dates
                        },
                        "auto_select": True
                    }
                )
                tasks.append(task)

            results = await self._orchestrator.run_tasks(tasks)

            return {
                "total": len(interview_requests),
                "results": [
                    {
                        "request_id": task.result.request_id if task.result else f"batch_{i}",
                        "status": task.result.status.value if task.result and not task.error else "failed",
                        "scheduled_time": task.result.scheduled_time.isoformat() if task.result and task.result.scheduled_time else None,
                        "meet_link": task.result.meet_link if task.result else None,
                        "error": str(task.error) if task.error else None
                    }
                    for i, task in enumerate(results.values())
                ]
            }

        else:
            raise ValueError(f"Unknown operation: {operation}")

    async def process_single_interview(self, interview_data: Dict[str, Any]) -> Dict[str, Any]:
        """単一面接を直接処理（API用）。"""
        if not self._orchestrator:
            raise RuntimeError("Interview orchestrator is not initialized")

        try:
            result = await schedule_interview_automatically(
                candidate_name=interview_data["candidate_name"],
                candidate_email=interview_data["candidate_email"],
                interviewer_names=interview_data["interviewer_names"],
                interviewer_emails=interview_data["interviewer_emails"],
                duration_minutes=interview_data.get("duration_minutes", 60),
                preferred_dates=interview_data.get("preferred_dates")
            )

            return {
                "request_id": result.request_id,
                "status": result.status.value,
                "scheduled_time": result.scheduled_time.isoformat() if result.scheduled_time else None,
                "meet_link": result.meet_link,
                "calendar_event_id": result.calendar_event_id,
                "email_message_id": result.email_message_id,
                "error": result.error_message
            }

        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }


class GoogleCalendarService(BaseService):
    """Google Calendar専用サービス。"""

    def __init__(
        self,
        name: str = "google-calendar-service",
        **kwargs,
    ):
        super().__init__(
            name=name,
            description="Google Calendar連携サービス",
            version="1.0.0",
            tags=["google", "calendar", "scheduling"],
            **kwargs,
        )

        self._calendar_agent: Optional[GoogleCalendarAgent] = None

    async def _on_start(self) -> None:
        """カレンダーエージェント初期化。"""
        self._calendar_agent = GoogleCalendarAgent()
        await self._calendar_agent.__aenter__()

    async def _on_stop(self) -> None:
        """カレンダーエージェント終了処理。"""
        if self._calendar_agent:
            await self._calendar_agent.__aexit__(None, None, None)
            self._calendar_agent = None

    async def _health_check(self) -> bool:
        """カレンダーサービスのヘルスチェック。"""
        return self._calendar_agent is not None

    async def _process_request(self, request: ServiceRequest) -> Any:
        """カレンダーリクエスト処理。"""
        if not self._calendar_agent:
            raise RuntimeError("Google Calendar agent is not initialized")

        operation = request.operation
        data = request.data

        task = Task(
            id=request.request_id,
            name=f"Calendar {operation}",
            data={"operation": operation, **data}
        )

        result = await self._calendar_agent.run_single_task(task)

        if result.error:
            raise Exception(f"Calendar operation failed: {result.error}")

        return result.result


class GmailService(BaseService):
    """Gmail専用サービス。"""

    def __init__(
        self,
        name: str = "gmail-service",
        **kwargs,
    ):
        super().__init__(
            name=name,
            description="Gmail通知サービス",
            version="1.0.0",
            tags=["google", "gmail", "email", "notification"],
            **kwargs,
        )

        self._gmail_agent: Optional[GmailAgent] = None

    async def _on_start(self) -> None:
        """Gmailエージェント初期化。"""
        self._gmail_agent = GmailAgent()
        await self._gmail_agent.__aenter__()

    async def _on_stop(self) -> None:
        """Gmailエージェント終了処理。"""
        if self._gmail_agent:
            await self._gmail_agent.__aexit__(None, None, None)
            self._gmail_agent = None

    async def _health_check(self) -> bool:
        """Gmailサービスのヘルスチェック。"""
        return self._gmail_agent is not None

    async def _process_request(self, request: ServiceRequest) -> Any:
        """Gmailリクエスト処理。"""
        if not self._gmail_agent:
            raise RuntimeError("Gmail agent is not initialized")

        operation = request.operation
        data = request.data

        task = Task(
            id=request.request_id,
            name=f"Gmail {operation}",
            data={"operation": operation, **data}
        )

        result = await self._gmail_agent.run_single_task(task)

        if result.error:
            raise Exception(f"Gmail operation failed: {result.error}")

        return result.result