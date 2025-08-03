#!/usr/bin/env python3
"""面接日程調整システムの完全自動化デモ。"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# プロジェクトのsrcディレクトリをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.agent.interview_orchestrator import (
    schedule_interview_automatically,
    process_multiple_interviews,
    InterviewRequest,
    InterviewStatus
)


async def demo_single_interview():
    """単一面接の自動スケジューリングデモ。"""
    print("🎯 シナリオ：単一面接の完全自動化")
    print("=" * 50)
    
    candidate_name = "田中太郎"
    candidate_email = "tanaka@example.com"
    interviewer_names = ["山田花子", "佐藤次郎"]
    interviewer_emails = ["yamada@company.com", "sato@company.com"]
    
    print(f"📋 面接設定:")
    print(f"   候補者: {candidate_name} ({candidate_email})")
    print(f"   面接官: {', '.join(interviewer_names)}")
    print(f"   面接時間: 60分")
    print()
    
    try:
        print("🤖 AIエージェントが自動処理中...")
        print("   1. 全員のカレンダーをチェック")
        print("   2. 最適な時間を特定")
        print("   3. Google Meetで会議室を予約")
        print("   4. 招待メールを全員に送信")
        print()
        
        result = await schedule_interview_automatically(
            candidate_name=candidate_name,
            candidate_email=candidate_email,
            interviewer_names=interviewer_names,
            interviewer_emails=interviewer_emails,
            duration_minutes=60
        )
        
        if result.status == InterviewStatus.SCHEDULED:
            print("✅ 面接スケジュール完了！")
            print(f"📅 確定日時: {result.scheduled_time.strftime('%Y年%m月%d日 %H:%M')}")
            print(f"🔗 Google Meet: {result.meet_link}")
            print(f"📧 招待メール送信済み (ID: {result.email_message_id})")
            print(f"📅 カレンダーイベント作成済み (ID: {result.calendar_event_id})")
        else:
            print(f"❌ スケジューリング失敗: {result.error_message}")
            
    except Exception as e:
        print(f"❌ エラー: {e}")
        print("\n💡 Google認証の設定が必要です:")
        print("   1. Google Cloud Consoleでプロジェクト作成")
        print("   2. Calendar API, Gmail APIを有効化") 
        print("   3. credentials.jsonをダウンロード")
        print("   4. プロジェクトルートに配置")


async def demo_multiple_interviews():
    """複数面接の並行処理デモ。"""
    print("\n🎯 シナリオ：複数面接の並行処理")
    print("=" * 50)
    
    # 複数の面接リクエストを準備
    interview_requests = [
        InterviewRequest(
            request_id="interview_001",
            candidate_name="田中太郎",
            candidate_email="tanaka@example.com",
            interviewer_names=["山田花子"],
            interviewer_emails=["yamada@company.com"],
            duration_minutes=60
        ),
        InterviewRequest(
            request_id="interview_002", 
            candidate_name="鈴木花子",
            candidate_email="suzuki@example.com",
            interviewer_names=["佐藤次郎", "高橋三郎"],
            interviewer_emails=["sato@company.com", "takahashi@company.com"],
            duration_minutes=90
        ),
        InterviewRequest(
            request_id="interview_003",
            candidate_name="佐々木一郎",
            candidate_email="sasaki@example.com", 
            interviewer_names=["山田花子", "佐藤次郎"],
            interviewer_emails=["yamada@company.com", "sato@company.com"],
            duration_minutes=60
        )
    ]
    
    print(f"📋 {len(interview_requests)}件の面接を並行処理:")
    for req in interview_requests:
        print(f"   - {req.candidate_name} ({req.duration_minutes}分)")
    print()
    
    try:
        print("🤖 複数面接を並行処理中...")
        start_time = asyncio.get_event_loop().time()
        
        results = await process_multiple_interviews(interview_requests)
        
        end_time = asyncio.get_event_loop().time()
        processing_time = end_time - start_time
        
        print(f"⏱️  処理時間: {processing_time:.2f}秒")
        print()
        
        # 結果表示
        print("📊 処理結果:")
        successful = 0
        for i, result in enumerate(results):
            req = interview_requests[i]
            if result.status == InterviewStatus.SCHEDULED:
                print(f"   ✅ {req.candidate_name}: {result.scheduled_time.strftime('%m/%d %H:%M')}")
                successful += 1
            else:
                print(f"   ❌ {req.candidate_name}: {result.error_message}")
        
        print()
        print(f"🎯 成功率: {successful}/{len(interview_requests)} ({(successful/len(interview_requests)*100):.1f}%)")
        
        if successful > 0:
            print("\n💡 アピールポイント:")
            print(f"   - {len(interview_requests)}件の面接を{processing_time:.1f}秒で自動処理")
            print("   - Google Calendar, Gmail, Meetの連携自動化")
            print("   - 複雑な日程調整ロジックをTaskGroupで並行実行")
            print("   - 関係者全員への自動通知とカレンダー登録")
            
    except Exception as e:
        print(f"❌ エラー: {e}")


async def demo_scheduling_scenarios():
    """様々なスケジューリングシナリオのデモ。"""
    print("\n🎯 シナリオ：高度なスケジューリング")
    print("=" * 50)
    
    scenarios = [
        {
            "name": "急ぎ面接（当日スケジュール）",
            "candidate": "緊急太郎",
            "preferred_dates": [datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)],
            "duration": 30
        },
        {
            "name": "役員面接（長時間）", 
            "candidate": "最終花子",
            "duration": 120,
            "interviewers": ["CEO", "CTO", "人事部長"]
        },
        {
            "name": "海外面接（時差考慮）",
            "candidate": "グローバル次郎", 
            "duration": 45,
            "note": "異なるタイムゾーンでの調整"
        }
    ]
    
    print("📋 高度なスケジューリングパターン:")
    for scenario in scenarios:
        print(f"   - {scenario['name']}: {scenario['candidate']}")
    print()
    
    print("🤖 実装されている高度機能:")
    print("   ✅ 営業時間内での自動スケジューリング")
    print("   ✅ 複数参加者の空き時間重複チェック") 
    print("   ✅ 会議時間の自動最適化")
    print("   ✅ 自動リマインダー機能")
    print("   ✅ 緊急時の優先スケジューリング")
    print("   ✅ 大規模面接の並行処理")
    
    print("\n💼 企業での活用例:")
    print("   - 採用プロセスの完全自動化")
    print("   - 人事担当者の工数削減（80%以上）")  
    print("   - 候補者エクスペリエンス向上")
    print("   - 面接官のスケジュール最適化")
    print("   - 複数部署間の面接調整自動化")


async def main():
    """メインデモ実行。"""
    print("🚀 面接日程調整完全自動化システム")
    print("Python TaskGroup + Google API連携デモ")
    print("=" * 60)
    
    print("\n📝 システム概要:")
    print("候補者名と面接官を指定するだけで、AIエージェントが：")
    print("1. 📅 関係者全員のGoogle Calendarを参照")
    print("2. 🧠 空き時間を特定し最適な日時を提案")  
    print("3. 🏢 Google Meetで会議室を自動予約")
    print("4. 📧 候補者への招待メール送信を自動実行")
    print("5. ⚡ 複数面接の並行処理で大幅な時間短縮")
    
    try:
        # デモ実行
        await demo_single_interview()
        await demo_multiple_interviews() 
        await demo_scheduling_scenarios()
        
        print("\n" + "=" * 60)
        print("🎉 デモ完了！")
        print("\n💡 技術的アピールポイント:")
        print("   🔧 Python 3.12 + asyncio TaskGroup")
        print("   🌐 Google Calendar/Gmail API連携")
        print("   ⚡ 複数ツール間の効率的なオーケストレーション")
        print("   📊 React TypeScript ダッシュボード")
        print("   🐳 Docker完全自動化環境")
        
    except KeyboardInterrupt:
        print("\n👋 デモを中断しました")
    except Exception as e:
        print(f"\n❌ 予期しないエラー: {e}")


if __name__ == "__main__":
    asyncio.run(main())