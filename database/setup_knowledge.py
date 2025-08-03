"""ナレッジベースデータをデータベースに挿入するスクリプト。"""

import asyncio
import sys
import os

# プロジェクトのsrcディレクトリをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.agent.database import DatabaseManager, KnowledgeItem
from knowledge_data import CLAUDE_CODE_KNOWLEDGE


async def setup_knowledge_base():
    """ナレッジベースデータをセットアップ。"""
    print("Claude Code ナレッジベースをセットアップ中...")

    async with DatabaseManager() as db:
        # データベース接続確認
        if not await db.health_check():
            print("❌ データベース接続に失敗しました")
            print("以下を確認してください：")
            print("1. Docker Composeでデータベースが起動している")
            print("2. .envファイルの設定が正しい")
            return False

        print("✅ データベース接続成功")

        # 既存のカテゴリを確認
        existing_categories = await db.get_all_categories()
        if existing_categories:
            print(f"既存のカテゴリ: {', '.join(existing_categories)}")

            # データがすでに存在する場合は確認
            response = input("データを追加しますか？ (y/N): ")
            if response.lower() != "y":
                print("セットアップをキャンセルしました")
                return True

        # ナレッジデータを挿入
        inserted_count = 0
        for knowledge_data in CLAUDE_CODE_KNOWLEDGE:
            try:
                item = KnowledgeItem(
                    title=knowledge_data["title"],
                    content=knowledge_data["content"],
                    category=knowledge_data["category"],
                    tags=knowledge_data["tags"],
                )

                item_id = await db.insert_knowledge(item)
                print(f"✅ 挿入完了: {item.title} (ID: {item_id})")
                inserted_count += 1

            except Exception as e:
                print(f"❌ 挿入失敗: {knowledge_data['title']} - {e}")

        print(
            f"\n🎉 セットアップ完了: {inserted_count}件のナレッジアイテムを挿入しました"
        )

        # カテゴリ別の統計を表示
        categories = await db.get_all_categories()
        print(f"利用可能なカテゴリ: {', '.join(categories)}")

        return True


async def test_search():
    """検索機能のテスト。"""
    print("\n🔍 検索機能をテスト中...")

    async with DatabaseManager() as db:
        # テスト検索
        test_queries = ["インストール", "TaskGroup", "エラー", "Python"]

        for query in test_queries:
            results = await db.search_knowledge(query, limit=3)
            print(f"\n検索クエリ: '{query}' -> {len(results)}件ヒット")
            for result in results:
                print(f"  - {result.title} ({result.category})")


async def main():
    """メイン実行関数。"""
    print("Claude Code ナレッジベース セットアップツール")
    print("=" * 50)

    try:
        # ナレッジベースセットアップ
        success = await setup_knowledge_base()
        if not success:
            return

        # 検索テスト
        await test_search()

        print("\n✨ すべての処理が完了しました！")
        print("データベースの確認: http://localhost:8080 (pgAdmin)")
        print("ユーザー: admin@example.com, パスワード: admin")

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        print("トラブルシューティング:")
        print("1. docker-compose up -d でデータベースを起動")
        print("2. .envファイルの設定を確認")
        print("3. uv sync で依存関係を確認")


if __name__ == "__main__":
    asyncio.run(main())
