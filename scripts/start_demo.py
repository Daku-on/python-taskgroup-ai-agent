"""RAGデモを簡単に実行するためのスクリプト。"""

import asyncio
import subprocess
import os
import sys

# プロジェクトのsrcディレクトリをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.agent.database import DatabaseManager


async def check_database():
    """データベース接続確認。"""
    try:
        db_manager = DatabaseManager()
        async with db_manager:
            return await db_manager.health_check()
    except Exception:
        return False


def start_database():
    """データベースを起動。"""
    print("🐳 PostgreSQLデータベースを起動中...")
    try:
        subprocess.run(
            ["docker-compose", "up", "-d", "postgres"],
            capture_output=True,
            text=True,
            check=True,
        )
        print("✅ データベース起動完了")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ データベース起動失敗: {e.stderr}")
        return False
    except FileNotFoundError:
        print("❌ Docker Composeが見つかりません。Dockerをインストールしてください。")
        return False


async def setup_knowledge():
    """ナレッジベースをセットアップ。"""
    print("📚 ナレッジベースをセットアップ中...")
    try:
        process = await asyncio.create_subprocess_exec(
            "uv",
            "run",
            "python",
            "database/setup_knowledge.py",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            print("✅ ナレッジベースセットアップ完了")
            return True
        else:
            print(f"❌ ナレッジベースセットアップ失敗: {stderr.decode()}")
            return False
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False


async def run_rag_demo():
    """RAGデモを実行。"""
    print("🤖 RAGエージェントデモを実行中...")
    try:
        process = await asyncio.create_subprocess_exec(
            "uv",
            "run",
            "python",
            "examples/rag_agent.py",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )

        # リアルタイム出力
        while True:
            line = await process.stdout.readline()
            if not line:
                break
            print(line.decode().rstrip())

        await process.communicate()
        return process.returncode == 0
    except Exception as e:
        print(f"❌ デモ実行エラー: {e}")
        return False


async def main():
    """メイン実行関数。"""
    print("🚀 Claude Code RAGエージェント 自動セットアップ & デモ")
    print("=" * 60)

    # 環境変数確認
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEYが設定されていません")
        print("以下の手順で設定してください：")
        print("1. .envファイルにOPENAI_API_KEYを追加")
        print("2. 再度このスクリプトを実行")
        return

    # ステップ1: データベース起動
    if not await check_database():
        print("📦 データベースが起動していません。起動します...")
        if not start_database():
            return

        # 起動待機
        print("⏳ データベース起動を待機中...")
        for i in range(30):
            await asyncio.sleep(1)
            if await check_database():
                print("✅ データベース接続確認")
                break
            if i % 5 == 0:
                print(f"   待機中... ({i + 1}/30秒)")
        else:
            print("❌ データベース起動タイムアウト")
            return
    else:
        print("✅ データベースは既に起動しています")

    # ステップ2: ナレッジベースセットアップ
    if not await setup_knowledge():
        return

    # ステップ3: RAGデモ実行
    print("\n" + "=" * 50)
    if await run_rag_demo():
        print("\n🎉 デモが正常に完了しました！")
        print("\n📊 次に試せること:")
        print("- pgAdmin: http://localhost:8080 (admin@example.com / admin)")
        print("- 直接デモ実行: uv run python examples/rag_agent.py")
        print("- カスタム質問: 上記ファイルを編集して独自の質問を追加")
    else:
        print("\n❌ デモ実行に失敗しました")
        print("詳細は上記のエラーメッセージを確認してください")


if __name__ == "__main__":
    asyncio.run(main())
