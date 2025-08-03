"""TaskGroupを使用したLLMベースのエージェント実装。"""

from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass
import aiohttp

from .base import BaseAgent, Task


@dataclass
class LLMConfig:
    """LLMエージェントの設定。"""

    api_url: str
    api_key: str
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    max_tokens: int = 1000
    timeout: int = 30


class LLMAgent(BaseAgent):
    """LLM APIとやり取りするAIエージェント。"""

    def __init__(
        self,
        name: str,
        config: LLMConfig,
        max_concurrent_tasks: int = 5,
        response_parser: Optional[Callable[[str], Any]] = None,
    ):
        super().__init__(name, max_concurrent_tasks)
        self.config = config
        self.response_parser = response_parser or (lambda x: x)
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self) -> "LLMAgent":
        """非同期コンテキストマネージャの開始。"""
        self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """非同期コンテキストマネージャの終了。"""
        if self._session:
            await self._session.close()

    async def process_task(self, task: Task) -> Any:
        """LLM APIコールを行ってタスクを処理。"""
        if not self._session:
            self._session = aiohttp.ClientSession()

        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }

        # リクエストペイロードを構築
        messages = task.data.get("messages", [])
        if not messages and "prompt" in task.data:
            messages = [{"role": "user", "content": task.data["prompt"]}]

        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": task.data.get("temperature", self.config.temperature),
            "max_tokens": task.data.get("max_tokens", self.config.max_tokens),
        }

        try:
            async with self._session.post(
                self.config.api_url,
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout),
            ) as response:
                response.raise_for_status()
                data = await response.json()

                # レスポンス内容を抽出
                content = (
                    data.get("choices", [{}])[0].get("message", {}).get("content", "")
                )

                # カスタムパーサーがあれば適用
                return self.response_parser(content)

        except aiohttp.ClientError as e:
            raise Exception(f"API request failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Task processing failed: {str(e)}")


class MultiAgentOrchestrator:
    """複数のエージェントを連携させて動作させるオーケストレーター。"""

    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}

    def register_agent(self, agent: BaseAgent) -> None:
        """エージェントをオーケストレーターに登録。"""
        self.agents[agent.name] = agent

    async def run_pipeline(
        self, pipeline: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """複数エージェントでタスクのパイプラインを実行。"""
        results = []

        for step in pipeline:
            agent_name = step.get("agent")
            tasks = step.get("tasks", [])

            if agent_name not in self.agents:
                raise ValueError(f"Agent {agent_name} not registered")

            agent = self.agents[agent_name]

            # タスク辞書をTaskオブジェクトに変換
            task_objects = [
                Task(
                    id=t.get("id", str(i)),
                    name=t.get("name", f"Task {i}"),
                    data=t.get("data", {}),
                )
                for i, t in enumerate(tasks)
            ]

            # このエージェント用のタスクを実行
            task_results = await agent.run_tasks(task_objects)

            # 結果を収集
            step_results = {
                "agent": agent_name,
                "results": {
                    task_id: {
                        "name": task.name,
                        "result": task.result,
                        "error": str(task.error) if task.error else None,
                    }
                    for task_id, task in task_results.items()
                },
            }
            results.append(step_results)

        return results
