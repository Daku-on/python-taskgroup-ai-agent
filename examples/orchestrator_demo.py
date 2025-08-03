"""オーケストレーションサービスのデモ。"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# プロジェクトのsrcディレクトリをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.services.orchestrator import OrchestratorService
from src.services.agent_services import (
    LLMAgentService,
    RAGAgentService,
    DatabaseService,
)
from src.services.base import ServiceRequest

# .envファイルから環境変数を読み込み
load_dotenv()


async def demo_service_registration():
    """サービス登録のデモ。"""
    print("=== サービス登録デモ ===")

    orchestrator = OrchestratorService()

    try:
        # オーケストレーター開始
        await orchestrator.start()
        print("✅ オーケストレーター開始")

        # 各種サービス作成・登録
        services = [
            DatabaseService(name="database-service"),
            LLMAgentService(name="llm-service"),
            RAGAgentService(name="rag-service"),
        ]

        for service in services:
            success = await orchestrator.registry.register_service(service)
            if success:
                print(f"✅ {service.name} 登録成功")
            else:
                print(f"❌ {service.name} 登録失敗")

        # 登録済みサービス一覧表示
        request = ServiceRequest(operation="get_services")
        response = await orchestrator.process_request(request)

        if response.success:
            services_data = response.data["services"]
            print(f"\n📋 登録済みサービス: {len(services_data)}個")
            for svc in services_data:
                print(
                    f"  - {svc['name']}: {svc['status']} (成功率: {svc['metrics']['success_rate']:.1f}%)"
                )

        return orchestrator

    except Exception as e:
        print(f"❌ サービス登録エラー: {e}")
        await orchestrator.stop()
        return None


async def demo_simple_workflow():
    """シンプルなワークフローのデモ。"""
    print("\n=== シンプルワークフローデモ ===")

    orchestrator = await demo_service_registration()
    if not orchestrator:
        return

    try:
        # ワークフロー定義
        workflow_steps = [
            {
                "step_id": "db_check",
                "service_name": "database-service",
                "operation": "get_categories",
                "data": {},
                "depends_on": [],
                "parallel": True,
            },
            {
                "step_id": "llm_generate",
                "service_name": "llm-service",
                "operation": "generate",
                "data": {
                    "messages": [
                        {
                            "role": "user",
                            "content": "Claude Codeについて簡潔に説明してください",
                        }
                    ]
                },
                "depends_on": [],
                "parallel": True,
            },
            {
                "step_id": "rag_question",
                "service_name": "rag-service",
                "operation": "question",
                "data": {"question": "Claude Codeのインストール方法を教えて"},
                "depends_on": ["db_check"],
                "parallel": False,
            },
        ]

        # ワークフロー実行
        print("🚀 ワークフロー実行開始...")
        request = ServiceRequest(
            operation="execute_workflow", data={"steps": workflow_steps}
        )

        response = await orchestrator.process_request(request)

        if response.success:
            workflow_id = response.data["workflow_id"]
            print(f"✅ ワークフロー開始: {workflow_id}")

            # ワークフロー完了待機
            await monitor_workflow(orchestrator, workflow_id)
        else:
            print(f"❌ ワークフロー開始失敗: {response.error_message}")

    finally:
        await orchestrator.stop()


async def demo_complex_workflow():
    """複雑なワークフローのデモ（並列処理とエラーハンドリング）。"""
    print("\n=== 複雑ワークフローデモ ===")

    orchestrator = await demo_service_registration()
    if not orchestrator:
        return

    try:
        # 複雑なワークフロー定義
        workflow_steps = [
            # Phase 1: データベース準備
            {
                "step_id": "db_categories",
                "service_name": "database-service",
                "operation": "get_categories",
                "data": {},
                "depends_on": [],
                "parallel": True,
            },
            # Phase 2: 並列LLM処理
            {
                "step_id": "llm_summary",
                "service_name": "llm-service",
                "operation": "generate",
                "data": {
                    "messages": [
                        {
                            "role": "user",
                            "content": "TaskGroupの利点を3つのポイントで説明",
                        }
                    ]
                },
                "depends_on": [],
                "parallel": True,
                "retry_count": 2,
            },
            {
                "step_id": "llm_comparison",
                "service_name": "llm-service",
                "operation": "generate",
                "data": {
                    "messages": [
                        {"role": "user", "content": "asyncioとTaskGroupの違いを説明"}
                    ]
                },
                "depends_on": [],
                "parallel": True,
                "retry_count": 2,
            },
            # Phase 3: RAG処理（Phase 1完了後）
            {
                "step_id": "rag_features",
                "service_name": "rag-service",
                "operation": "question",
                "data": {"question": "Claude Codeの主要機能について詳しく教えて"},
                "depends_on": ["db_categories"],
                "parallel": False,
            },
            {
                "step_id": "rag_troubleshoot",
                "service_name": "rag-service",
                "operation": "question",
                "data": {"question": "Claude Codeでエラーが出た場合の対処法は？"},
                "depends_on": ["db_categories"],
                "parallel": False,
            },
            # Phase 4: バッチRAG処理（Phase 2とPhase 3完了後）
            {
                "step_id": "rag_batch",
                "service_name": "rag-service",
                "operation": "batch_questions",
                "data": {
                    "questions": [
                        "TaskGroupとは何ですか？",
                        "パフォーマンス最適化の方法は？",
                        "サポートされているプログラミング言語は？",
                    ]
                },
                "depends_on": ["llm_summary", "llm_comparison", "rag_features"],
                "parallel": False,
                "timeout": 60.0,
            },
        ]

        # ワークフロー実行
        print("🚀 複雑ワークフロー実行開始...")
        request = ServiceRequest(
            operation="execute_workflow", data={"steps": workflow_steps}
        )

        response = await orchestrator.process_request(request)

        if response.success:
            workflow_id = response.data["workflow_id"]
            print(f"✅ ワークフロー開始: {workflow_id}")

            # ワークフロー完了待機
            await monitor_workflow(orchestrator, workflow_id, detailed=True)
        else:
            print(f"❌ ワークフロー開始失敗: {response.error_message}")

    finally:
        await orchestrator.stop()


async def monitor_workflow(orchestrator, workflow_id: str, detailed: bool = False):
    """ワークフロー監視。"""
    print(f"📊 ワークフロー {workflow_id} を監視中...")

    while True:
        # ワークフロー状態取得
        request = ServiceRequest(
            operation="get_workflow_status", data={"workflow_id": workflow_id}
        )

        response = await orchestrator.process_request(request)

        if response.success:
            status_data = response.data
            status = status_data["status"]
            completed = status_data["steps_completed"]
            total = status_data["steps_total"]

            print(f"  状態: {status}, 進捗: {completed}/{total}")

            if detailed and status_data.get("errors"):
                for error in status_data["errors"]:
                    print(f"  ❌ エラー: {error}")

            if status in ["completed", "failed", "cancelled"]:
                break

        await asyncio.sleep(2.0)

    # 最終結果表示
    if response.success:
        status_data = response.data
        duration = None

        if status_data["started_at"] and status_data["completed_at"]:
            from datetime import datetime

            start = datetime.fromisoformat(status_data["started_at"])
            end = datetime.fromisoformat(status_data["completed_at"])
            duration = (end - start).total_seconds()

        print(f"🏁 ワークフロー完了: {status_data['status']}")
        if duration:
            print(f"⏱️ 実行時間: {duration:.2f}秒")

        if status_data.get("errors"):
            print(f"❌ エラー数: {len(status_data['errors'])}")


async def demo_orchestrator_stats():
    """オーケストレーター統計情報のデモ。"""
    print("\n=== オーケストレーター統計デモ ===")

    orchestrator = await demo_service_registration()
    if not orchestrator:
        return

    try:
        # 統計情報取得
        stats = await orchestrator.get_orchestrator_stats()

        print("📈 オーケストレーター統計:")
        print(f"  - 総ワークフロー数: {stats['total_workflows']}")
        print(f"  - 成功率: {stats['success_rate']:.1f}%")
        print(f"  - アクティブワークフロー: {stats['active_workflows']}")
        print(f"  - 登録サービス数: {stats['registered_services']}")
        print(f"  - 実行中サービス数: {stats['running_services']}")

        print("\n🔍 サービス健康状態:")
        for service_name, health in stats["service_health"].items():
            print(f"  - {service_name}: {health}")

    finally:
        await orchestrator.stop()


async def main():
    """メイン実行関数。"""
    print("🎭 オーケストレーションサービス デモ")
    print("=" * 50)

    try:
        # 環境確認
        if not os.getenv("OPENAI_API_KEY"):
            print("❌ OPENAI_API_KEYが設定されていません")
            print("以下の手順で設定してください：")
            print("1. .envファイルにOPENAI_API_KEYを追加")
            return

        # 各種デモ実行
        print("🎬 デモ1: サービス登録")
        orchestrator = await demo_service_registration()
        if orchestrator:
            await orchestrator.stop()

        print("\n🎬 デモ2: シンプルワークフロー")
        await demo_simple_workflow()

        print("\n🎬 デモ3: 複雑ワークフロー")
        await demo_complex_workflow()

        print("\n🎬 デモ4: 統計情報")
        await demo_orchestrator_stats()

        print("\n🎉 全デモが完了しました！")
        print("\n💡 このデモでは以下を確認できます：")
        print("- 複数サービスの自動登録・管理")
        print("- ワークフローの依存関係解決")
        print("- 並列・直列処理の混在")
        print("- エラーハンドリングとリトライ")
        print("- リアルタイム監視と統計")

    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        print("\nトラブルシューティング:")
        print("1. docker-compose up -d でデータベースを起動")
        print("2. uv run python database/setup_knowledge.py でデータをセットアップ")
        print("3. .envファイルの設定を確認")


if __name__ == "__main__":
    asyncio.run(main())
