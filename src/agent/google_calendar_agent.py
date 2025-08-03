"""Google Calendar連携エージェント。"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json
import os
from dataclasses import dataclass

from .base import BaseAgent, Task
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


@dataclass
class TimeSlot:
    """時間枠を表すクラス。"""
    start: datetime
    end: datetime
    attendees: List[str]
    
    def overlaps_with(self, other: 'TimeSlot') -> bool:
        """他の時間枠と重複するかチェック。"""
        return (self.start < other.end) and (self.end > other.start)
    
    def __str__(self) -> str:
        return f"{self.start.strftime('%Y-%m-%d %H:%M')} - {self.end.strftime('%H:%M')}"


@dataclass
class AvailabilityRequest:
    """空き時間検索リクエスト。"""
    attendees: List[str]  # 参加者のメールアドレス
    duration_minutes: int  # 面接時間（分）
    preferred_dates: List[datetime]  # 希望日程
    business_hours_start: int = 9  # 営業時間開始（時）
    business_hours_end: int = 18  # 営業時間終了（時）
    timezone: str = 'Asia/Tokyo'


@dataclass
class InterviewSchedule:
    """面接スケジュール。"""
    start_time: datetime
    end_time: datetime
    attendees: List[str]
    candidate_name: str
    interviewer_names: List[str]
    room_name: Optional[str] = None
    meet_link: Optional[str] = None
    calendar_event_id: Optional[str] = None


class GoogleCalendarAgent(BaseAgent):
    """Google Calendar連携エージェント。"""
    
    SCOPES = [
        'https://www.googleapis.com/auth/calendar',
        'https://www.googleapis.com/auth/calendar.events'
    ]
    
    def __init__(self, name: str = "GoogleCalendarAgent", max_concurrent_tasks: int = 5):
        super().__init__(name, max_concurrent_tasks)
        self.service = None
        self._credentials = None
    
    async def __aenter__(self):
        """非同期コンテキスト開始。"""
        await self._authenticate()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキスト終了。"""
        pass
    
    async def _authenticate(self):
        """Google認証を実行。"""
        creds = None
        token_file = 'token.json'
        credentials_file = 'credentials.json'
        
        # 既存のトークンを読み込み
        if os.path.exists(token_file):
            creds = Credentials.from_authorized_user_file(token_file, self.SCOPES)
        
        # 有効な認証情報がない場合は再認証
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(credentials_file):
                    raise FileNotFoundError(
                        f"Google認証ファイル {credentials_file} が見つかりません。"
                        "Google Cloud Consoleから認証情報をダウンロードしてください。"
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_file, self.SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            # トークンを保存
            with open(token_file, 'w') as token:
                token.write(creds.to_json())
        
        self._credentials = creds
        self.service = build('calendar', 'v3', credentials=creds)
    
    async def process_task(self, task: Task) -> Any:
        """タスクを処理。"""
        operation = task.data.get('operation')
        
        if operation == 'find_availability':
            return await self._find_availability(task.data)
        elif operation == 'create_event':
            return await self._create_event(task.data)
        elif operation == 'get_busy_times':
            return await self._get_busy_times(task.data)
        elif operation == 'update_event':
            return await self._update_event(task.data)
        elif operation == 'delete_event':
            return await self._delete_event(task.data)
        else:
            raise ValueError(f"未対応の操作: {operation}")
    
    async def _find_availability(self, data: Dict[str, Any]) -> List[TimeSlot]:
        """参加者全員の空き時間を検索。"""
        request = AvailabilityRequest(**data['request'])
        
        # 各参加者の空き時間を取得
        busy_times = []
        for attendee in request.attendees:
            busy = await self._get_busy_times({
                'email': attendee,
                'start_date': request.preferred_dates[0],
                'end_date': request.preferred_dates[-1] + timedelta(days=1)
            })
            busy_times.extend(busy)
        
        # 希望日程での空き時間を計算
        available_slots = []
        duration = timedelta(minutes=request.duration_minutes)
        
        for date in request.preferred_dates:
            # 営業時間内で30分刻みのスロットをチェック
            current_time = date.replace(
                hour=request.business_hours_start, 
                minute=0, 
                second=0, 
                microsecond=0
            )
            end_time = date.replace(
                hour=request.business_hours_end, 
                minute=0, 
                second=0, 
                microsecond=0
            )
            
            while current_time + duration <= end_time:
                slot = TimeSlot(
                    start=current_time,
                    end=current_time + duration,
                    attendees=request.attendees
                )
                
                # 既存の会議と重複チェック
                if not any(slot.overlaps_with(busy) for busy in busy_times):
                    available_slots.append(slot)
                
                current_time += timedelta(minutes=30)  # 30分刻み
        
        return available_slots[:10]  # 最大10個の候補を返す
    
    async def _get_busy_times(self, data: Dict[str, Any]) -> List[TimeSlot]:
        """指定ユーザーの忙しい時間を取得。"""
        email = data['email']
        start_date = data['start_date']
        end_date = data['end_date']
        
        # FreeBusy APIを使用して忙しい時間を取得
        body = {
            'timeMin': start_date.isoformat(),
            'timeMax': end_date.isoformat(),
            'items': [{'id': email}]
        }
        
        try:
            freebusy_result = self.service.freebusy().query(body=body).execute()
            calendars = freebusy_result.get('calendars', {})
            
            busy_times = []
            if email in calendars:
                for busy_period in calendars[email].get('busy', []):
                    start_time = datetime.fromisoformat(
                        busy_period['start'].replace('Z', '+00:00')
                    )
                    end_time = datetime.fromisoformat(
                        busy_period['end'].replace('Z', '+00:00')
                    )
                    
                    busy_times.append(TimeSlot(
                        start=start_time,
                        end=end_time,
                        attendees=[email]
                    ))
            
            return busy_times
            
        except Exception as e:
            print(f"忙しい時間取得エラー ({email}): {e}")
            return []
    
    async def _create_event(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """カレンダーイベントを作成。"""
        schedule = InterviewSchedule(**data['schedule'])
        
        # Google Meetリンクを自動生成
        event = {
            'summary': f'面接: {schedule.candidate_name}',
            'description': f'候補者: {schedule.candidate_name}\\n面接官: {", ".join(schedule.interviewer_names)}',
            'start': {
                'dateTime': schedule.start_time.isoformat(),
                'timeZone': 'Asia/Tokyo',
            },
            'end': {
                'dateTime': schedule.end_time.isoformat(),
                'timeZone': 'Asia/Tokyo',
            },
            'attendees': [{'email': email} for email in schedule.attendees],
            'conferenceData': {
                'createRequest': {
                    'requestId': f'interview-{schedule.candidate_name}-{int(schedule.start_time.timestamp())}',
                    'conferenceSolutionKey': {'type': 'hangoutsMeet'}
                }
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},  # 1日前
                    {'method': 'popup', 'minutes': 30},       # 30分前
                ],
            },
        }
        
        try:
            # イベント作成
            created_event = self.service.events().insert(
                calendarId='primary', 
                body=event,
                conferenceDataVersion=1,
                sendUpdates='all'  # 全参加者に通知送信
            ).execute()
            
            # Google MeetリンクとイベントIDを取得
            meet_link = None
            if 'conferenceData' in created_event:
                meet_link = created_event['conferenceData'].get('entryPoints', [{}])[0].get('uri')
            
            return {
                'event_id': created_event['id'],
                'meet_link': meet_link,
                'html_link': created_event.get('htmlLink'),
                'status': 'created',
                'attendees_notified': True
            }
            
        except Exception as e:
            raise Exception(f"カレンダーイベント作成エラー: {e}")
    
    async def _update_event(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """カレンダーイベントを更新。"""
        event_id = data['event_id']
        updates = data['updates']
        
        try:
            # 既存イベントを取得
            event = self.service.events().get(
                calendarId='primary', 
                eventId=event_id
            ).execute()
            
            # 更新内容を適用
            for key, value in updates.items():
                event[key] = value
            
            # イベント更新
            updated_event = self.service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=event,
                sendUpdates='all'
            ).execute()
            
            return {
                'event_id': updated_event['id'],
                'status': 'updated',
                'attendees_notified': True
            }
            
        except Exception as e:
            raise Exception(f"カレンダーイベント更新エラー: {e}")
    
    async def _delete_event(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """カレンダーイベントを削除。"""
        event_id = data['event_id']
        
        try:
            self.service.events().delete(
                calendarId='primary',
                eventId=event_id,
                sendUpdates='all'
            ).execute()
            
            return {
                'event_id': event_id,
                'status': 'deleted',
                'attendees_notified': True
            }
            
        except Exception as e:
            raise Exception(f"カレンダーイベント削除エラー: {e}")


# 使用例とヘルパー関数
async def find_interview_slots(
    candidate_email: str,
    interviewer_emails: List[str], 
    duration_minutes: int = 60,
    preferred_dates: Optional[List[datetime]] = None
) -> List[TimeSlot]:
    """面接可能な時間枠を検索。"""
    
    if preferred_dates is None:
        # デフォルト: 今日から1週間
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        preferred_dates = [today + timedelta(days=i) for i in range(7)]
    
    async with GoogleCalendarAgent() as agent:
        task = Task(
            id="find_availability",
            name="面接空き時間検索",
            data={
                'operation': 'find_availability',
                'request': {
                    'attendees': [candidate_email] + interviewer_emails,
                    'duration_minutes': duration_minutes,
                    'preferred_dates': preferred_dates,
                    'business_hours_start': 9,
                    'business_hours_end': 18
                }
            }
        )
        
        result = await agent.run_single_task(task)
        return result.result


async def schedule_interview(
    candidate_name: str,
    candidate_email: str,
    interviewer_names: List[str],
    interviewer_emails: List[str],
    start_time: datetime,
    duration_minutes: int = 60
) -> Dict[str, Any]:
    """面接をスケジュール。"""
    
    end_time = start_time + timedelta(minutes=duration_minutes)
    
    schedule = InterviewSchedule(
        start_time=start_time,
        end_time=end_time,
        attendees=[candidate_email] + interviewer_emails,
        candidate_name=candidate_name,
        interviewer_names=interviewer_names
    )
    
    async with GoogleCalendarAgent() as agent:
        task = Task(
            id="create_event",
            name="面接イベント作成",
            data={
                'operation': 'create_event',
                'schedule': {
                    'start_time': schedule.start_time,
                    'end_time': schedule.end_time,
                    'attendees': schedule.attendees,
                    'candidate_name': schedule.candidate_name,
                    'interviewer_names': schedule.interviewer_names
                }
            }
        )
        
        result = await agent.run_single_task(task)
        return result.result