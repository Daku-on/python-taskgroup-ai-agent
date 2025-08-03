"""サービス管理ダッシュボードのシンプル実装。"""

import asyncio
import os
import sys
from datetime import datetime
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


class ServiceDashboard:
    """サービス管理ダッシュボード。"""

    def __init__(self):
        self.orchestrator = OrchestratorService()
        self.running = False

    async def start(self) -> bool:
        """ダッシュボード開始。"""
        try:
            await self.orchestrator.start()
            self.running = True

            # デフォルトサービス登録
            await self._register_default_services()

            print("🎛️ サービスダッシュボード開始")
            return True

        except Exception as e:
            print(f"❌ ダッシュボード開始失敗: {e}")
            return False

    async def stop(self):
        """ダッシュボード停止。"""
        if self.running:
            await self.orchestrator.stop()
            self.running = False
            print("🛑 サービスダッシュボード停止")

    async def _register_default_services(self):
        """デフォルトサービス登録。"""
        services = [
            DatabaseService(name="database"),
            LLMAgentService(name="llm"),
            RAGAgentService(name="rag"),
        ]

        for service in services:
            try:
                success = await self.orchestrator.registry.register_service(service)
                if success:
                    print(f"✅ {service.name}サービス登録")
                else:
                    print(f"⚠️ {service.name}サービス登録失敗")
            except Exception as e:
                print(f"❌ {service.name}サービス登録エラー: {e}")

    async def show_dashboard(self):
        """ダッシュボード表示。"""
        while self.running:
            # 画面クリア
            os.system("clear" if os.name == "posix" else "cls")

            print("=" * 80)
            print("🎛️  サービス管理ダッシュボード")
            print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 80)

            # サービス一覧表示
            await self._show_services()

            # オーケストレーター統計
            await self._show_orchestrator_stats()

            # メニュー表示
            self._show_menu()

            # ユーザー入力待機（非ブロッキング）
            try:
                choice = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None, input, "選択してください (1-6, Enter=更新): "
                    ),
                    timeout=5.0,
                )

                await self._handle_menu_choice(choice.strip())

            except asyncio.TimeoutError:
                # タイムアウト時は自動更新
                continue
            except KeyboardInterrupt:
                print("\n🛑 ダッシュボード終了")
                break

    async def _show_services(self):
        """サービス一覧表示。"""
        print("\n📋 登録済みサービス:")
        print("-" * 80)

        try:
            request = ServiceRequest(operation="get_services")
            response = await self.orchestrator.process_request(request)

            if response.success:
                services = response.data["services"]

                if not services:
                    print("  (サービスが登録されていません)")
                else:
                    print(
                        f"{'サービス名':<20} {'状態':<12} {'成功率':<8} {'平均応答':<10} {'総リクエスト':<10}"
                    )
                    print("-" * 80)

                    for svc in services:
                        metrics = svc["metrics"]
                        print(
                            f"{svc['name']:<20} "
                            f"{svc['status']:<12} "
                            f"{metrics['success_rate']:>6.1f}% "
                            f"{metrics['average_response_time']:>8.2f}s "
                            f"{metrics['total_requests']:>10}"
                        )
            else:
                print(f"  ❌ サービス情報取得失敗: {response.error_message}")

        except Exception as e:
            print(f"  ❌ エラー: {e}")

    async def _show_orchestrator_stats(self):
        """オーケストレーター統計表示。"""
        print("\n📊 オーケストレーター統計:")
        print("-" * 40)

        try:
            stats = await self.orchestrator.get_orchestrator_stats()

            print(f"  総ワークフロー数: {stats['total_workflows']}")
            print(f"  成功ワークフロー: {stats['successful_workflows']}")
            print(f"  失敗ワークフロー: {stats['failed_workflows']}")
            print(f"  成功率: {stats['success_rate']:.1f}%")
            print(f"  アクティブワークフロー: {stats['active_workflows']}")
            print(
                f"  実行中サービス: {stats['running_services']}/{stats['registered_services']}"
            )

        except Exception as e:
            print(f"  ❌ 統計取得エラー: {e}")

    def _show_menu(self):
        """メニュー表示。"""
        print("\n🔧 操作メニュー:")
        print("  1. LLMテスト実行")
        print("  2. RAG質問実行")
        print("  3. シンプルワークフロー実行")
        print("  4. サービス詳細表示")
        print("  5. サービス再起動")
        print("  6. 終了")
        print("  Enter. ダッシュボード更新")

    async def _handle_menu_choice(self, choice: str):
        """メニュー選択処理。"""
        if choice == "1":
            await self._test_llm_service()
        elif choice == "2":
            await self._test_rag_service()
        elif choice == "3":
            await self._run_simple_workflow()
        elif choice == "4":
            await self._show_service_details()
        elif choice == "5":
            await self._restart_service()
        elif choice == "6":
            self.running = False
        elif choice == "":
            # ダッシュボード更新（何もしない）
            pass
        else:
            print("❌ 無効な選択です")
            await asyncio.sleep(1)

    async def _test_llm_service(self):
        """LLMサービステスト。"""
        print("\n🤖 LLMサービステスト実行中...")

        service = self.orchestrator.registry.find_service_by_name("llm")
        if not service:
            print("❌ LLMサービスが見つかりません")
            await asyncio.sleep(2)
            return

        try:
            request = ServiceRequest(
                operation="generate",
                data={
                    "messages": [
                        {"role": "user", "content": "こんにちは！調子はどうですか？"}
                    ]
                },
            )

            response = await service.process_request(request)

            if response.success:
                text = response.data.get("text", "")
                print(f"✅ LLM応答: {text[:100]}...")
                print(f"⏱️ 実行時間: {response.execution_time:.2f}秒")
            else:
                print(f"❌ LLMテスト失敗: {response.error_message}")

        except Exception as e:
            print(f"❌ LLMテストエラー: {e}")

        await asyncio.sleep(3)

    async def _test_rag_service(self):
        """RAGサービステスト。"""
        print("\n🔍 RAGサービステスト実行中...")

        service = self.orchestrator.registry.find_service_by_name("rag")
        if not service:
            print("❌ RAGサービスが見つかりません")
            await asyncio.sleep(2)
            return

        try:
            request = ServiceRequest(
                operation="question",
                data={"question": "Claude Codeの基本的な機能を教えて"},
            )

            response = await service.process_request(request)

            if response.success:
                data = response.data
                print(f"✅ RAG応答: {data['answer'][:100]}...")
                print(f"🗃️ データベース使用: {'Yes' if data['used_database'] else 'No'}")
                print(f"📚 参照ソース数: {len(data['sources'])}")
                print(f"⏱️ 実行時間: {response.execution_time:.2f}秒")
            else:
                print(f"❌ RAGテスト失敗: {response.error_message}")

        except Exception as e:
            print(f"❌ RAGテストエラー: {e}")

        await asyncio.sleep(3)

    async def _run_simple_workflow(self):
        """シンプルワークフロー実行。"""
        print("\n🔄 シンプルワークフロー実行中...")

        workflow_steps = [
            {
                "step_id": "llm_greeting",
                "service_name": "llm",
                "operation": "generate",
                "data": {
                    "messages": [
                        {"role": "user", "content": "TaskGroupについて1行で説明して"}
                    ]
                },
                "depends_on": [],
                "parallel": True,
            },
            {
                "step_id": "rag_features",
                "service_name": "rag",
                "operation": "question",
                "data": {"question": "Claude Codeの特徴を教えて"},
                "depends_on": [],
                "parallel": True,
            },
        ]

        try:
            request = ServiceRequest(
                operation="execute_workflow", data={"steps": workflow_steps}
            )

            response = await self.orchestrator.process_request(request)

            if response.success:
                workflow_id = response.data["workflow_id"]
                print(f"✅ ワークフロー開始: {workflow_id}")

                # 完了まで待機
                await self._wait_for_workflow(workflow_id)
            else:
                print(f"❌ ワークフロー開始失敗: {response.error_message}")

        except Exception as e:
            print(f"❌ ワークフローエラー: {e}")

        await asyncio.sleep(3)

    async def _wait_for_workflow(self, workflow_id: str):
        """ワークフロー完了待機。"""
        for _ in range(30):  # 最大60秒待機
            try:
                request = ServiceRequest(
                    operation="get_workflow_status", data={"workflow_id": workflow_id}
                )

                response = await self.orchestrator.process_request(request)

                if response.success:
                    status = response.data["status"]
                    print(f"  状態: {status}")

                    if status in ["completed", "failed", "cancelled"]:
                        break

                await asyncio.sleep(2)

            except Exception:
                break

    async def _show_service_details(self):
        """サービス詳細表示。"""
        print("\n📋 サービス詳細:")

        services = self.orchestrator.registry.get_all_services()
        for i, service in enumerate(services, 1):
            info = await service.get_info()
            print(f"\n{i}. {info.name}")
            print(f"   ID: {info.service_id}")
            print(f"   状態: {info.status.value}")
            print(f"   説明: {info.description}")
            print(f"   タグ: {', '.join(info.tags)}")
            print(f"   作成日時: {info.created_at.strftime('%Y-%m-%d %H:%M:%S')}")

        await asyncio.sleep(5)

    async def _restart_service(self):
        """サービス再起動。"""
        services = self.orchestrator.registry.get_all_services()

        print("\n🔄 再起動するサービスを選択:")
        for i, service in enumerate(services, 1):
            print(f"  {i}. {service.name}")

        try:
            choice = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None, input, "選択 (1-{}): ".format(len(services))
                ),
                timeout=10.0,
            )

            idx = int(choice.strip()) - 1
            if 0 <= idx < len(services):
                service = services[idx]
                print(f"🔄 {service.name} を再起動中...")

                success = await service.restart()
                if success:
                    print(f"✅ {service.name} 再起動成功")
                else:
                    print(f"❌ {service.name} 再起動失敗")
            else:
                print("❌ 無効な選択です")

        except (asyncio.TimeoutError, ValueError):
            print("❌ 無効な入力です")

        await asyncio.sleep(2)


async def main():
    """メイン実行関数。"""
    print("🎛️ サービス管理ダッシュボード")
    print("=" * 50)

    # 環境確認
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEYが設定されていません")
        print("設定してからダッシュボードを開始してください")
        return

    dashboard = ServiceDashboard()

    try:
        # ダッシュボード開始
        success = await dashboard.start()
        if not success:
            return

        # ダッシュボード表示
        await dashboard.show_dashboard()

    except KeyboardInterrupt:
        print("\n🛑 ダッシュボード終了")
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
    finally:
        await dashboard.stop()


if __name__ == "__main__":
    asyncio.run(main())
