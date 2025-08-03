"""Gmail通知エージェント。"""

import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

from .base import BaseAgent, Task
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


@dataclass
class EmailTemplate:
    """メールテンプレート。"""
    subject: str
    body_text: str
    body_html: Optional[str] = None


@dataclass
class InterviewNotification:
    """面接通知情報。"""
    candidate_name: str
    candidate_email: str
    interviewer_names: List[str]
    interviewer_emails: List[str]
    interview_datetime: datetime
    meet_link: str
    calendar_link: str
    duration_minutes: int = 60


class GmailAgent(BaseAgent):
    """Gmail通知エージェント。"""
    
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/gmail.compose'
    ]
    
    def __init__(self, name: str = "GmailAgent", max_concurrent_tasks: int = 10):
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
        """Google認証を実行（Calendar Agentと共通）。"""
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
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_file, self.SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            # トークンを保存
            with open(token_file, 'w') as token:
                token.write(creds.to_json())
        
        self._credentials = creds
        self.service = build('gmail', 'v1', credentials=creds)
    
    async def process_task(self, task: Task) -> Any:
        """タスクを処理。"""
        operation = task.data.get('operation')
        
        if operation == 'send_interview_invitation':
            return await self._send_interview_invitation(task.data)
        elif operation == 'send_interview_confirmation':
            return await self._send_interview_confirmation(task.data)
        elif operation == 'send_interview_reminder':
            return await self._send_interview_reminder(task.data)
        elif operation == 'send_interview_cancellation':
            return await self._send_interview_cancellation(task.data)
        elif operation == 'send_custom_email':
            return await self._send_custom_email(task.data)
        else:
            raise ValueError(f"未対応の操作: {operation}")
    
    def _create_interview_invitation_template(self, notification: InterviewNotification) -> EmailTemplate:
        """面接招待メールテンプレートを作成。"""
        interview_date = notification.interview_datetime.strftime('%Y年%m月%d日')
        interview_time = notification.interview_datetime.strftime('%H:%M')
        interviewer_list = "、".join(notification.interviewer_names)
        
        subject = f"面接のご案内 - {interview_date} {interview_time}"
        
        body_text = f"""
{notification.candidate_name} 様

この度は弊社求人にご応募いただき、誠にありがとうございます。
書類選考の結果、面接をさせていただくことになりました。

■ 面接詳細
日時: {interview_date}（{notification.interview_datetime.strftime('%A')}） {interview_time} - {(notification.interview_datetime.replace(minute=notification.interview_datetime.minute + notification.duration_minutes)).strftime('%H:%M')}
面接官: {interviewer_list}
実施方法: オンライン面接（Google Meet）

■ 参加方法
以下のリンクから面接にご参加ください：
{notification.meet_link}

■ カレンダー登録
カレンダーに登録される場合は、以下のリンクをご利用ください：
{notification.calendar_link}

■ 事前準備
- 安定したインターネット接続をご確認ください
- Google Meetが利用できる環境を整えてください
- 履歴書・職務経歴書をお手元にご用意ください

何かご不明な点がございましたら、お気軽にお問い合わせください。

どうぞよろしくお願いいたします。

採用担当
"""
        
        body_html = f"""
<html>
<body>
<p>{notification.candidate_name} 様</p>

<p>この度は弊社求人にご応募いただき、誠にありがとうございます。<br>
書類選考の結果、面接をさせていただくことになりました。</p>

<h3>■ 面接詳細</h3>
<ul>
<li><strong>日時:</strong> {interview_date}（{notification.interview_datetime.strftime('%A')}） {interview_time} - {(notification.interview_datetime.replace(minute=notification.interview_datetime.minute + notification.duration_minutes)).strftime('%H:%M')}</li>
<li><strong>面接官:</strong> {interviewer_list}</li>
<li><strong>実施方法:</strong> オンライン面接（Google Meet）</li>
</ul>

<h3>■ 参加方法</h3>
<p><a href="{notification.meet_link}" style="background-color: #4285f4; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">面接に参加する</a></p>

<h3>■ カレンダー登録</h3>
<p><a href="{notification.calendar_link}">カレンダーに追加</a></p>

<h3>■ 事前準備</h3>
<ul>
<li>安定したインターネット接続をご確認ください</li>
<li>Google Meetが利用できる環境を整えてください</li>
<li>履歴書・職務経歴書をお手元にご用意ください</li>
</ul>

<p>何かご不明な点がございましたら、お気軽にお問い合わせください。</p>

<p>どうぞよろしくお願いいたします。</p>

<p>採用担当</p>
</body>
</html>
"""
        
        return EmailTemplate(
            subject=subject,
            body_text=body_text,
            body_html=body_html
        )
    
    def _create_confirmation_template(self, notification: InterviewNotification) -> EmailTemplate:
        """面接確定通知テンプレートを作成。"""
        interview_date = notification.interview_datetime.strftime('%Y年%m月%d日')
        interview_time = notification.interview_datetime.strftime('%H:%M')
        
        subject = f"面接確定のお知らせ - {interview_date} {interview_time}"
        
        body_text = f"""
{notification.candidate_name} 様

面接日程が確定いたしましたのでお知らせします。

■ 確定した面接詳細
日時: {interview_date} {interview_time}
Google Meet: {notification.meet_link}

面接当日はどうぞよろしくお願いいたします。

採用担当
"""
        
        return EmailTemplate(subject=subject, body_text=body_text)
    
    def _create_reminder_template(self, notification: InterviewNotification) -> EmailTemplate:
        """面接リマインダーテンプレートを作成。"""
        interview_date = notification.interview_datetime.strftime('%Y年%m月%d日')
        interview_time = notification.interview_datetime.strftime('%H:%M')
        
        subject = f"【明日】面接のリマインダー - {interview_date} {interview_time}"
        
        body_text = f"""
{notification.candidate_name} 様

明日の面接のリマインダーです。

■ 面接詳細
日時: {interview_date} {interview_time}
Google Meet: {notification.meet_link}

準備はいかがでしょうか。お待ちしております。

採用担当
"""
        
        return EmailTemplate(subject=subject, body_text=body_text)
    
    def _create_cancellation_template(self, notification: InterviewNotification, reason: str) -> EmailTemplate:
        """面接キャンセル通知テンプレートを作成。"""
        interview_date = notification.interview_datetime.strftime('%Y年%m月%d日')
        interview_time = notification.interview_datetime.strftime('%H:%M')
        
        subject = f"面接キャンセルのお知らせ - {interview_date} {interview_time}"
        
        body_text = f"""
{notification.candidate_name} 様

誠に申し訳ございませんが、{interview_date} {interview_time}の面接をキャンセルさせていただきます。

理由: {reason}

再度日程調整をさせていただきますので、お待ちください。

採用担当
"""
        
        return EmailTemplate(subject=subject, body_text=body_text)
    
    async def _send_interview_invitation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """面接招待メールを送信。"""
        notification = InterviewNotification(**data['notification'])
        template = self._create_interview_invitation_template(notification)
        
        return await self._send_email(
            to_email=notification.candidate_email,
            template=template,
            cc_emails=notification.interviewer_emails
        )
    
    async def _send_interview_confirmation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """面接確定通知を送信。"""
        notification = InterviewNotification(**data['notification'])
        template = self._create_confirmation_template(notification)
        
        return await self._send_email(
            to_email=notification.candidate_email,
            template=template
        )
    
    async def _send_interview_reminder(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """面接リマインダーを送信。"""
        notification = InterviewNotification(**data['notification'])
        template = self._create_reminder_template(notification)
        
        return await self._send_email(
            to_email=notification.candidate_email,
            template=template
        )
    
    async def _send_interview_cancellation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """面接キャンセル通知を送信。"""
        notification = InterviewNotification(**data['notification'])
        reason = data.get('reason', '社内都合により')
        template = self._create_cancellation_template(notification, reason)
        
        return await self._send_email(
            to_email=notification.candidate_email,
            template=template
        )
    
    async def _send_custom_email(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """カスタムメールを送信。"""
        template = EmailTemplate(**data['template'])
        
        return await self._send_email(
            to_email=data['to_email'],
            template=template,
            cc_emails=data.get('cc_emails'),
            bcc_emails=data.get('bcc_emails')
        )
    
    async def _send_email(
        self,
        to_email: str,
        template: EmailTemplate,
        cc_emails: Optional[List[str]] = None,
        bcc_emails: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """メールを送信。"""
        try:
            # MIMEメッセージを作成
            if template.body_html:
                message = MIMEMultipart('alternative')
                text_part = MIMEText(template.body_text, 'plain', 'utf-8')
                html_part = MIMEText(template.body_html, 'html', 'utf-8')
                message.attach(text_part)
                message.attach(html_part)
            else:
                message = MIMEText(template.body_text, 'plain', 'utf-8')
            
            # ヘッダー設定
            message['to'] = to_email
            message['subject'] = template.subject
            
            if cc_emails:
                message['cc'] = ', '.join(cc_emails)
            if bcc_emails:
                message['bcc'] = ', '.join(bcc_emails)
            
            # メール送信
            raw_message = base64.urlsafe_b64encode(
                message.as_bytes()
            ).decode('utf-8')
            
            send_result = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            return {
                'message_id': send_result['id'],
                'status': 'sent',
                'to_email': to_email,
                'subject': template.subject,
                'sent_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            raise Exception(f"メール送信エラー: {e}")


# ヘルパー関数
async def send_interview_invitation(
    candidate_name: str,
    candidate_email: str,
    interviewer_names: List[str],
    interviewer_emails: List[str],
    interview_datetime: datetime,
    meet_link: str,
    calendar_link: str,
    duration_minutes: int = 60
) -> Dict[str, Any]:
    """面接招待メールを送信。"""
    
    notification = InterviewNotification(
        candidate_name=candidate_name,
        candidate_email=candidate_email,
        interviewer_names=interviewer_names,
        interviewer_emails=interviewer_emails,
        interview_datetime=interview_datetime,
        meet_link=meet_link,
        calendar_link=calendar_link,
        duration_minutes=duration_minutes
    )
    
    async with GmailAgent() as agent:
        task = Task(
            id="send_invitation",
            name="面接招待メール送信",
            data={
                'operation': 'send_interview_invitation',
                'notification': {
                    'candidate_name': notification.candidate_name,
                    'candidate_email': notification.candidate_email,
                    'interviewer_names': notification.interviewer_names,
                    'interviewer_emails': notification.interviewer_emails,
                    'interview_datetime': notification.interview_datetime,
                    'meet_link': notification.meet_link,
                    'calendar_link': notification.calendar_link,
                    'duration_minutes': notification.duration_minutes
                }
            }
        )
        
        result = await agent.run_single_task(task)
        return result.result


async def send_bulk_notifications(
    notifications: List[InterviewNotification],
    notification_type: str = 'invitation'
) -> List[Dict[str, Any]]:
    """複数の面接通知を一括送信。"""
    
    async with GmailAgent() as agent:
        tasks = []
        
        for i, notification in enumerate(notifications):
            task = Task(
                id=f"bulk_notification_{i}",
                name=f"面接通知送信 {i+1}",
                data={
                    'operation': f'send_interview_{notification_type}',
                    'notification': {
                        'candidate_name': notification.candidate_name,
                        'candidate_email': notification.candidate_email,
                        'interviewer_names': notification.interviewer_names,
                        'interviewer_emails': notification.interviewer_emails,
                        'interview_datetime': notification.interview_datetime,
                        'meet_link': notification.meet_link,
                        'calendar_link': notification.calendar_link,
                        'duration_minutes': notification.duration_minutes
                    }
                }
            )
            tasks.append(task)
        
        results = await agent.run_tasks(tasks)
        return [task.result for task in results.values()]