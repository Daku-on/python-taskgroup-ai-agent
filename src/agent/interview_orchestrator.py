"""面接日程調整オーケストレーター。"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from .base import BaseAgent, Task
from .google_calendar_agent import GoogleCalendarAgent, TimeSlot, find_interview_slots, schedule_interview
from .gmail_agent import GmailAgent, InterviewNotification, send_interview_invitation


class InterviewStatus(Enum):
    """面接ステータス。"""
    PENDING = "pending"           # 日程調整中
    SCHEDULED = "scheduled"       # 日程確定
    CONFIRMED = "confirmed"       # 参加者確認済み
    COMPLETED = "completed"       # 面接完了
    CANCELLED = "cancelled"       # キャンセル


@dataclass
class InterviewRequest:
    """面接リクエスト。"""
    request_id: str
    candidate_name: str
    candidate_email: str
    interviewer_names: List[str]
    interviewer_emails: List[str]
    duration_minutes: int = 60
    preferred_dates: Optional[List[datetime]] = None
    requirements: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.preferred_dates is None:
            # デフォルト: 明日から1週間の営業日
            tomorrow = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            self.preferred_dates = []
            for i in range(7):
                date = tomorrow + timedelta(days=i)
                # 平日のみ（月-金）
                if date.weekday() < 5:
                    self.preferred_dates.append(date)


@dataclass
class InterviewScheduleResult:
    """面接スケジュール結果。"""
    request_id: str
    status: InterviewStatus
    scheduled_time: Optional[datetime] = None
    meet_link: Optional[str] = None
    calendar_event_id: Optional[str] = None
    email_message_id: Optional[str] = None
    available_slots: Optional[List[TimeSlot]] = None
    error_message: Optional[str] = None


class InterviewOrchestrator(BaseAgent):
    """面接日程調整オーケストレーター。"""
    
    def __init__(self, name: str = "InterviewOrchestrator", max_concurrent_tasks: int = 5):
        super().__init__(name, max_concurrent_tasks)
        self.calendar_agent = None
        self.gmail_agent = None
    
    async def __aenter__(self):
        """非同期コンテキスト開始。"""
        self.calendar_agent = GoogleCalendarAgent()
        self.gmail_agent = GmailAgent()
        await self.calendar_agent.__aenter__()
        await self.gmail_agent.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキスト終了。"""
        if self.calendar_agent:
            await self.calendar_agent.__aexit__(exc_type, exc_val, exc_tb)
        if self.gmail_agent:
            await self.gmail_agent.__aexit__(exc_type, exc_val, exc_tb)
    
    async def process_task(self, task: Task) -> Any:
        """タスクを処理。"""
        operation = task.data.get('operation')
        
        if operation == 'schedule_complete_interview':
            return await self._schedule_complete_interview(task.data)
        elif operation == 'find_available_slots':
            return await self._find_available_slots(task.data)
        elif operation == 'confirm_interview_slot':
            return await self._confirm_interview_slot(task.data)
        elif operation == 'reschedule_interview':
            return await self._reschedule_interview(task.data)
        elif operation == 'cancel_interview':
            return await self._cancel_interview(task.data)
        else:
            raise ValueError(f"未対応の操作: {operation}")
    
    async def _schedule_complete_interview(self, data: Dict[str, Any]) -> InterviewScheduleResult:
        """完全自動面接スケジューリング。"""
        request = InterviewRequest(**data['request'])
        auto_select = data.get('auto_select', True)
        
        try:
            # 1. 空き時間を検索
            print(f"📅 {request.candidate_name}の面接可能時間を検索中...")
            available_slots = await find_interview_slots(
                candidate_email=request.candidate_email,
                interviewer_emails=request.interviewer_emails,
                duration_minutes=request.duration_minutes,
                preferred_dates=request.preferred_dates
            )
            
            if not available_slots:
                return InterviewScheduleResult(
                    request_id=request.request_id,
                    status=InterviewStatus.PENDING,
                    available_slots=[],
                    error_message="指定期間に空き時間が見つかりませんでした"
                )
            
            # 2. 最適な時間枠を自動選択（または候補を返す）
            if auto_select:
                selected_slot = available_slots[0]  # 最初の候補を選択
                print(f"⏰ 自動選択: {selected_slot}")
                
                # 3. カレンダーイベント作成
                print("📝 カレンダーイベントを作成中...")
                calendar_result = await schedule_interview(
                    candidate_name=request.candidate_name,
                    candidate_email=request.candidate_email,
                    interviewer_names=request.interviewer_names,
                    interviewer_emails=request.interviewer_emails,
                    start_time=selected_slot.start,
                    duration_minutes=request.duration_minutes
                )
                
                # 4. 招待メール送信
                print("📧 招待メールを送信中...")
                notification = InterviewNotification(
                    candidate_name=request.candidate_name,
                    candidate_email=request.candidate_email,
                    interviewer_names=request.interviewer_names,
                    interviewer_emails=request.interviewer_emails,
                    interview_datetime=selected_slot.start,
                    meet_link=calendar_result['meet_link'],
                    calendar_link=calendar_result['html_link'],
                    duration_minutes=request.duration_minutes
                )
                
                email_result = await send_interview_invitation(
                    candidate_name=notification.candidate_name,
                    candidate_email=notification.candidate_email,
                    interviewer_names=notification.interviewer_names,
                    interviewer_emails=notification.interviewer_emails,
                    interview_datetime=notification.interview_datetime,
                    meet_link=notification.meet_link,
                    calendar_link=notification.calendar_link,
                    duration_minutes=notification.duration_minutes
                )
                
                print("✅ 面接スケジュール完了！")
                
                return InterviewScheduleResult(
                    request_id=request.request_id,
                    status=InterviewStatus.SCHEDULED,
                    scheduled_time=selected_slot.start,
                    meet_link=calendar_result['meet_link'],
                    calendar_event_id=calendar_result['event_id'],
                    email_message_id=email_result['message_id']
                )
            
            else:
                # 候補一覧を返す
                return InterviewScheduleResult(
                    request_id=request.request_id,
                    status=InterviewStatus.PENDING,
                    available_slots=available_slots
                )
                
        except Exception as e:
            return InterviewScheduleResult(
                request_id=request.request_id,
                status=InterviewStatus.PENDING,
                error_message=str(e)
            )
    
    async def _find_available_slots(self, data: Dict[str, Any]) -> List[TimeSlot]:
        """利用可能な時間枠を検索。"""
        request = InterviewRequest(**data['request'])
        
        return await find_interview_slots(
            candidate_email=request.candidate_email,
            interviewer_emails=request.interviewer_emails,
            duration_minutes=request.duration_minutes,
            preferred_dates=request.preferred_dates
        )
    
    async def _confirm_interview_slot(self, data: Dict[str, Any]) -> InterviewScheduleResult:
        """指定された時間枠で面接を確定。"""
        request = InterviewRequest(**data['request'])
        selected_slot = TimeSlot(**data['selected_slot'])
        
        try:
            # カレンダーイベント作成
            calendar_result = await schedule_interview(
                candidate_name=request.candidate_name,
                candidate_email=request.candidate_email,
                interviewer_names=request.interviewer_names,
                interviewer_emails=request.interviewer_emails,
                start_time=selected_slot.start,
                duration_minutes=request.duration_minutes
            )
            
            # 招待メール送信
            email_result = await send_interview_invitation(
                candidate_name=request.candidate_name,
                candidate_email=request.candidate_email,
                interviewer_names=request.interviewer_names,
                interviewer_emails=request.interviewer_emails,
                interview_datetime=selected_slot.start,
                meet_link=calendar_result['meet_link'],
                calendar_link=calendar_result['html_link'],
                duration_minutes=request.duration_minutes
            )
            
            return InterviewScheduleResult(
                request_id=request.request_id,
                status=InterviewStatus.SCHEDULED,
                scheduled_time=selected_slot.start,
                meet_link=calendar_result['meet_link'],
                calendar_event_id=calendar_result['event_id'],
                email_message_id=email_result['message_id']
            )
            
        except Exception as e:
            return InterviewScheduleResult(
                request_id=request.request_id,
                status=InterviewStatus.PENDING,
                error_message=str(e)
            )
    
    async def _reschedule_interview(self, data: Dict[str, Any]) -> InterviewScheduleResult:
        """面接を再スケジュール。"""
        request = InterviewRequest(**data['request'])
        old_event_id = data['old_event_id']
        new_slot = TimeSlot(**data['new_slot'])
        
        try:
            # 古いイベントを削除
            await self.calendar_agent.process_task(Task(
                id="delete_old_event",
                name="古いイベント削除",
                data={
                    'operation': 'delete_event',
                    'event_id': old_event_id
                }
            ))
            
            # 新しいイベントを作成
            calendar_result = await schedule_interview(
                candidate_name=request.candidate_name,
                candidate_email=request.candidate_email,
                interviewer_names=request.interviewer_names,
                interviewer_emails=request.interviewer_emails,
                start_time=new_slot.start,
                duration_minutes=request.duration_minutes
            )
            
            return InterviewScheduleResult(
                request_id=request.request_id,
                status=InterviewStatus.SCHEDULED,
                scheduled_time=new_slot.start,
                meet_link=calendar_result['meet_link'],
                calendar_event_id=calendar_result['event_id']
            )
            
        except Exception as e:
            return InterviewScheduleResult(
                request_id=request.request_id,
                status=InterviewStatus.PENDING,
                error_message=str(e)
            )
    
    async def _cancel_interview(self, data: Dict[str, Any]) -> InterviewScheduleResult:
        """面接をキャンセル。"""
        request = InterviewRequest(**data['request'])
        event_id = data['event_id']
        reason = data.get('reason', '社内都合により')
        
        try:
            # カレンダーイベントを削除
            await self.calendar_agent.process_task(Task(
                id="delete_event",
                name="イベント削除",
                data={
                    'operation': 'delete_event',
                    'event_id': event_id
                }
            ))
            
            # キャンセル通知を送信
            await self.gmail_agent.process_task(Task(
                id="send_cancellation",
                name="キャンセル通知",
                data={
                    'operation': 'send_interview_cancellation',
                    'notification': {
                        'candidate_name': request.candidate_name,
                        'candidate_email': request.candidate_email,
                        'interviewer_names': request.interviewer_names,
                        'interviewer_emails': request.interviewer_emails,
                        'interview_datetime': datetime.now(),  # ダミー
                        'meet_link': '',
                        'calendar_link': ''
                    },
                    'reason': reason
                }
            ))
            
            return InterviewScheduleResult(
                request_id=request.request_id,
                status=InterviewStatus.CANCELLED
            )
            
        except Exception as e:
            return InterviewScheduleResult(
                request_id=request.request_id,
                status=InterviewStatus.PENDING,
                error_message=str(e)
            )


# ヘルパー関数
async def schedule_interview_automatically(
    candidate_name: str,
    candidate_email: str,
    interviewer_names: List[str],
    interviewer_emails: List[str],
    duration_minutes: int = 60,
    preferred_dates: Optional[List[datetime]] = None
) -> InterviewScheduleResult:
    """面接を完全自動でスケジュール。"""
    
    request = InterviewRequest(
        request_id=f"auto_{candidate_name}_{int(datetime.now().timestamp())}",
        candidate_name=candidate_name,
        candidate_email=candidate_email,
        interviewer_names=interviewer_names,
        interviewer_emails=interviewer_emails,
        duration_minutes=duration_minutes,
        preferred_dates=preferred_dates
    )
    
    async with InterviewOrchestrator() as orchestrator:
        task = Task(
            id="schedule_complete",
            name="完全自動面接スケジューリング",
            data={
                'operation': 'schedule_complete_interview',
                'request': {
                    'request_id': request.request_id,
                    'candidate_name': request.candidate_name,
                    'candidate_email': request.candidate_email,
                    'interviewer_names': request.interviewer_names,
                    'interviewer_emails': request.interviewer_emails,
                    'duration_minutes': request.duration_minutes,
                    'preferred_dates': request.preferred_dates
                },
                'auto_select': True
            }
        )
        
        result = await orchestrator.run_single_task(task)
        return result.result


async def process_multiple_interviews(
    interview_requests: List[InterviewRequest]
) -> List[InterviewScheduleResult]:
    """複数の面接を並行処理。"""
    
    async with InterviewOrchestrator() as orchestrator:
        tasks = []
        
        for i, request in enumerate(interview_requests):
            task = Task(
                id=f"interview_{i}",
                name=f"面接スケジューリング {request.candidate_name}",
                data={
                    'operation': 'schedule_complete_interview',
                    'request': {
                        'request_id': request.request_id,
                        'candidate_name': request.candidate_name,
                        'candidate_email': request.candidate_email,
                        'interviewer_names': request.interviewer_names,
                        'interviewer_emails': request.interviewer_emails,
                        'duration_minutes': request.duration_minutes,
                        'preferred_dates': request.preferred_dates
                    },
                    'auto_select': True
                }
            )
            tasks.append(task)
        
        results = await orchestrator.run_tasks(tasks)
        return [task.result for task in results.values()]