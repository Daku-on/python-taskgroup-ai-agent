"""エージェント機能のテスト。"""

import asyncio
import pytest
import sys
import os

# テスト用にsrcディレクトリをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.agent.base import BaseAgent, Task
from src.agent.llm_agent import LLMConfig, MultiAgentOrchestrator


class TestAgent(BaseAgent):
    """テスト用の簡単なエージェント。"""

    async def process_task(self, task: Task):
        """テスト用タスク処理（遅延をシミュレート）。"""
        await asyncio.sleep(0.1)  # 短い遅延
        return f"processed: {task.name}"


@pytest.mark.asyncio
async def test_base_agent_single_task():
    """基本エージェントの単一タスクテスト。"""
    agent = TestAgent("TestAgent")
    task = Task(id="1", name="test task", data={})

    result = await agent.run_single_task(task)

    assert result.id == "1"
    assert result.result == "processed: test task"
    assert result.error is None
    assert result.completed_at is not None


@pytest.mark.asyncio
async def test_base_agent_multiple_tasks():
    """基本エージェントの複数タスクテスト。"""
    agent = TestAgent("TestAgent", max_concurrent_tasks=2)

    tasks = [
        Task(id="1", name="task 1", data={}),
        Task(id="2", name="task 2", data={}),
        Task(id="3", name="task 3", data={}),
    ]

    start_time = asyncio.get_event_loop().time()
    results = await agent.run_tasks(tasks)
    end_time = asyncio.get_event_loop().time()

    # すべてのタスクが完了していることを確認
    assert len(results) == 3
    for task_id, task in results.items():
        assert task.result.startswith("processed:")
        assert task.error is None
        assert task.completed_at is not None

    # 並行実行により実行時間が短縮されていることを確認（概算）
    # 3つのタスクを直列実行すると0.3秒、並行実行（2並列）なら0.2秒程度
    assert end_time - start_time < 0.25  # 余裕をもって0.25秒以下


@pytest.mark.asyncio
async def test_agent_error_handling():
    """エージェントのエラーハンドリングテスト。"""

    class ErrorAgent(BaseAgent):
        async def process_task(self, task: Task):
            if task.name == "error_task":
                raise ValueError("Test error")
            return "success"

    agent = ErrorAgent("ErrorAgent")
    tasks = [
        Task(id="1", name="normal_task", data={}),
        Task(id="2", name="error_task", data={}),
    ]

    results = await agent.run_tasks(tasks)

    # 正常タスクは成功
    assert results["1"].result == "success"
    assert results["1"].error is None

    # エラータスクは失敗
    assert results["2"].result is None
    assert isinstance(results["2"].error, ValueError)
    assert str(results["2"].error) == "Test error"


@pytest.mark.asyncio
async def test_multi_agent_orchestrator():
    """マルチエージェントオーケストレーターのテスト。"""
    orchestrator = MultiAgentOrchestrator()

    # テストエージェントを登録
    agent1 = TestAgent("Agent1")
    agent2 = TestAgent("Agent2")

    orchestrator.register_agent(agent1)
    orchestrator.register_agent(agent2)

    # パイプライン定義
    pipeline = [
        {
            "agent": "Agent1",
            "tasks": [
                {"id": "1", "name": "task1", "data": {}},
                {"id": "2", "name": "task2", "data": {}},
            ],
        },
        {
            "agent": "Agent2",
            "tasks": [
                {"id": "3", "name": "task3", "data": {}},
            ],
        },
    ]

    results = await orchestrator.run_pipeline(pipeline)

    # 2つのステップが実行されていることを確認
    assert len(results) == 2

    # Agent1のステップ
    step1 = results[0]
    assert step1["agent"] == "Agent1"
    assert len(step1["results"]) == 2
    assert step1["results"]["1"]["result"] == "processed: task1"
    assert step1["results"]["2"]["result"] == "processed: task2"

    # Agent2のステップ
    step2 = results[1]
    assert step2["agent"] == "Agent2"
    assert len(step2["results"]) == 1
    assert step2["results"]["3"]["result"] == "processed: task3"


def test_llm_config():
    """LLM設定のテスト。"""
    config = LLMConfig(
        api_url="https://api.example.com",
        api_key="test-key",
        model="test-model",
        temperature=0.5,
        max_tokens=500,
    )

    assert config.api_url == "https://api.example.com"
    assert config.api_key == "test-key"
    assert config.model == "test-model"
    assert config.temperature == 0.5
    assert config.max_tokens == 500
