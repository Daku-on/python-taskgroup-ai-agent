"""OpenAI APIを使用したAIエージェントの実装例。"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# プロジェクトのsrcディレクトリをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.agent.llm_agent import LLMAgent, LLMConfig
from src.agent.base import Task

# .envファイルから環境変数を読み込み
load_dotenv()


class OpenAIAgent(LLMAgent):
    """OpenAI APIと連携するエージェント。"""

    @classmethod
    def from_env(cls, name: str = "OpenAI-Agent", max_concurrent_tasks: int = 3):
        """環境変数からOpenAIエージェントを作成。"""
        config = LLMConfig(
            api_url=os.getenv(
                "OPENAI_API_URL", "https://api.openai.com/v1/chat/completions"
            ),
            api_key=os.getenv("OPENAI_API_KEY", ""),
            model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
            temperature=0.7,
            max_tokens=1000,
        )

        if not config.api_key:
            raise ValueError("OPENAI_API_KEY is not set in environment variables")

        return cls(name, config, max_concurrent_tasks)


async def demo_single_task():
    """単一タスクのデモ。"""
    print("=== 単一タスクデモ ===")

    async with OpenAIAgent.from_env("SingleAgent") as agent:
        task = Task(
            id="story",
            name="短編小説生成",
            data={
                "messages": [
                    {
                        "role": "user",
                        "content": "AIと人間が協力する短い物語を書いてください（200文字以内）",
                    }
                ],
                "temperature": 0.8,
                "max_tokens": 200,
            },
        )

        print(f"タスク開始: {task.name}")
        result = await agent.run_single_task(task)

        if result.error:
            print(f"エラー: {result.error}")
        else:
            print(f"結果:\n{result.result}\n")


async def demo_multiple_tasks():
    """複数タスクの並行実行デモ。"""
    print("=== 複数タスク並行実行デモ ===")

    async with OpenAIAgent.from_env("MultiAgent", max_concurrent_tasks=3) as agent:
        tasks = [
            Task(
                id="translate",
                name="翻訳タスク",
                data={
                    "messages": [
                        {
                            "role": "user",
                            "content": "Please translate 'Hello, world!' to Japanese",
                        }
                    ]
                },
            ),
            Task(
                id="summary",
                name="要約タスク",
                data={
                    "messages": [
                        {
                            "role": "user",
                            "content": "以下の文章を一言で要約してください：\n機械学習は人工知能の一分野で、コンピューターがデータから学習し、明示的にプログラムされることなく改善する能力を指します。",
                        }
                    ]
                },
            ),
            Task(
                id="coding",
                name="コード生成タスク",
                data={
                    "messages": [
                        {
                            "role": "user",
                            "content": "Pythonでフィボナッチ数列を計算する関数を書いてください（短く）",
                        }
                    ]
                },
            ),
        ]

        print(f"{len(tasks)}個のタスクを並行実行中...")
        start_time = asyncio.get_event_loop().time()

        results = await agent.run_tasks(tasks)

        end_time = asyncio.get_event_loop().time()

        print(f"実行時間: {end_time - start_time:.2f}秒\n")

        # 結果を表示
        for task_id, task in results.items():
            print(f"タスク: {task.name}")
            if task.error:
                print(f"  エラー: {task.error}")
            else:
                print(
                    f"  結果: {task.result[:100]}{'...' if len(str(task.result)) > 100 else ''}"
                )
            print()


async def main():
    """メイン実行関数。"""
    print("OpenAI APIエージェント デモ")
    print("=" * 40)

    try:
        # 環境変数チェック
        if not os.getenv("OPENAI_API_KEY"):
            print("エラー: OPENAI_API_KEYが設定されていません")
            print("以下の手順で設定してください：")
            print("1. .envファイルを作成")
            print("2. OPENAI_API_KEY=your-api-key-here を追加")
            return

        await demo_single_task()
        await demo_multiple_tasks()

    except Exception as e:
        print(f"予期しないエラー: {e}")


if __name__ == "__main__":
    asyncio.run(main())
