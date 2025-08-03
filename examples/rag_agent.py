"""RAG（検索拡張生成）エージェントのデモ。"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# プロジェクトのsrcディレクトリをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.agent.smart_agent import SmartKnowledgeAgent, BatchKnowledgeAgent
from src.agent.llm_agent import LLMConfig
from src.agent.database import DatabaseManager

# .envファイルから環境変数を読み込み
load_dotenv()


async def demo_single_question():
    """単一質問のRAGデモ。"""
    print("=== 単一質問RAGデモ ===")

    # LLM設定
    config = LLMConfig(
        api_url=os.getenv(
            "OPENAI_API_URL", "https://api.openai.com/v1/chat/completions"
        ),
        api_key=os.getenv("OPENAI_API_KEY", ""),
        model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
        temperature=0.7,
    )

    if not config.api_key:
        print("❌ OPENAI_API_KEYが設定されていません")
        return

    # データベースマネージャー
    db_manager = DatabaseManager()

    # スマートエージェント作成
    async with SmartKnowledgeAgent("RAG-Agent", config, db_manager) as agent:
        # データベース接続確認
        if not await db_manager.health_check():
            print("❌ データベース接続に失敗しました")
            print("データベースを起動してください: docker-compose up -d")
            return

        print("✅ データベース接続成功")

        # テスト質問
        test_questions = [
            "Claude Codeをインストールする方法を教えて",
            "今日の天気はどうですか？",  # 関係ない質問
            "TaskGroupの機能について詳しく教えて",
            "Pythonでフィボナッチ数列を作る方法は？",  # 一般的な質問
            "Claude Codeでエラーが出た時はどうすればいい？",
        ]

        for i, question in enumerate(test_questions, 1):
            print(f"\n--- 質問 {i}: {question} ---")

            from src.agent.base import Task

            task = Task(id=f"q{i}", name=f"質問{i}", data={"question": question})

            try:
                response = await agent.run_single_task(task)
                result = response.result

                print(f"🤖 データベース使用: {'✅' if result.used_database else '❌'}")
                print(f"💭 判断理由: {result.decision_reasoning}")

                if result.sources:
                    print(f"📚 参照ソース ({len(result.sources)}件):")
                    for source in result.sources:
                        print(f"  - {source.title} ({source.category})")

                print(f"💬 回答:\n{result.answer}")

            except Exception as e:
                print(f"❌ エラー: {e}")


async def demo_batch_questions():
    """複数質問の並行処理RAGデモ。"""
    print("\n=== 複数質問並行処理RAGデモ ===")

    # LLM設定
    config = LLMConfig(
        api_url=os.getenv(
            "OPENAI_API_URL", "https://api.openai.com/v1/chat/completions"
        ),
        api_key=os.getenv("OPENAI_API_KEY", ""),
        model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
        temperature=0.7,
    )

    if not config.api_key:
        print("❌ OPENAI_API_KEYが設定されていません")
        return

    # データベースマネージャー
    db_manager = DatabaseManager()

    # スマートエージェントとバッチエージェント作成
    async with SmartKnowledgeAgent("RAG-Agent", config, db_manager) as smart_agent:
        batch_agent = BatchKnowledgeAgent(smart_agent, max_concurrent_tasks=3)

        # バッチ処理用質問
        batch_questions = [
            "Claude Codeの基本的な機能は何ですか？",
            "TypeScriptのサポート状況を教えて",
            "パフォーマンス最適化の方法は？",
            "デバッグ機能について詳しく教えて",
            "プロジェクト管理機能はありますか？",
        ]

        print(f"{len(batch_questions)}個の質問を並行処理中...")
        start_time = asyncio.get_event_loop().time()

        # 並行処理実行
        responses = await batch_agent.process_questions(batch_questions)

        end_time = asyncio.get_event_loop().time()

        print(f"⏱️ 処理時間: {end_time - start_time:.2f}秒")
        print("📊 統計情報:")

        db_used_count = sum(1 for r in responses if r.used_database)
        total_sources = sum(len(r.sources) for r in responses)

        print(f"  - データベース利用: {db_used_count}/{len(responses)}件")
        print(f"  - 参照ソース総数: {total_sources}件")

        # 結果詳細
        print("\n📋 詳細結果:")
        for i, (question, response) in enumerate(zip(batch_questions, responses), 1):
            print(f"\n{i}. {question}")
            print(f"   DB使用: {'✅' if response.used_database else '❌'}")
            if response.sources:
                print(
                    f"   ソース: {', '.join(s.title for s in response.sources[:2])}{'...' if len(response.sources) > 2 else ''}"
                )
            print(f"   回答: {response.answer[:100]}...")


async def demo_database_stats():
    """データベース統計情報表示。"""
    print("\n=== データベース統計 ===")

    db_manager = DatabaseManager()
    async with db_manager:
        if not await db_manager.health_check():
            print("❌ データベース接続に失敗")
            return

        # カテゴリ統計
        categories = await db_manager.get_all_categories()
        print(f"📂 利用可能なカテゴリ: {len(categories)}個")

        for category in categories:
            items = await db_manager.get_by_category(category, limit=100)
            print(f"  - {category}: {len(items)}件")

        # 検索テスト
        print("\n🔍 検索テスト:")
        test_searches = ["インストール", "エラー", "Python", "最適化"]
        for search_term in test_searches:
            results = await db_manager.search_knowledge(search_term, limit=3)
            print(f"  '{search_term}': {len(results)}件ヒット")


async def main():
    """メイン実行関数。"""
    print("🚀 Claude Code RAGエージェント デモ")
    print("=" * 50)

    try:
        # 環境確認
        if not os.getenv("OPENAI_API_KEY"):
            print("❌ OPENAI_API_KEYが設定されていません")
            print("以下の手順で設定してください：")
            print("1. .envファイルにOPENAI_API_KEYを追加")
            return

        # データベース統計
        await demo_database_stats()

        # 単一質問デモ
        await demo_single_question()

        # バッチ処理デモ
        await demo_batch_questions()

        print("\n🎉 すべてのデモが完了しました！")
        print("\n💡 このデモでは以下を確認できます：")
        print("- 質問内容によるデータベース検索の自動判断")
        print("- 関連ナレッジの検索と活用")
        print("- 複数質問の並行処理")
        print("- TaskGroupによる効率的な並行実行")

    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        print("\nトラブルシューティング:")
        print("1. docker-compose up -d でデータベースを起動")
        print("2. uv run python database/setup_knowledge.py でデータをセットアップ")
        print("3. .envファイルの設定を確認")


if __name__ == "__main__":
    asyncio.run(main())
