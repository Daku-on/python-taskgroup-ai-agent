"""既存エージェントのサービス化実装。"""

from typing import Any, Optional
import os
from dotenv import load_dotenv

from .base import BaseService, ServiceRequest
from ..agent.base import Task
from ..agent.llm_agent import LLMAgent, LLMConfig
from ..agent.smart_agent import SmartKnowledgeAgent, AgentResponse
from ..agent.database import DatabaseManager

load_dotenv()


class LLMAgentService(BaseService):
    """LLMエージェントのサービス実装。"""

    def __init__(
        self,
        name: str = "llm-agent-service",
        llm_config: Optional[LLMConfig] = None,
        **kwargs,
    ):
        super().__init__(
            name=name,
            description="LLM API との連携を提供するサービス",
            version="1.0.0",
            tags=["llm", "ai", "openai"],
            **kwargs,
        )

        self.llm_config = llm_config or self._create_default_config()
        self._llm_agent: Optional[LLMAgent] = None

    def _create_default_config(self) -> LLMConfig:
        """デフォルトのLLM設定を作成。"""
        return LLMConfig(
            api_url=os.getenv(
                "OPENAI_API_URL", "https://api.openai.com/v1/chat/completions"
            ),
            api_key=os.getenv("OPENAI_API_KEY", ""),
            model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
            temperature=0.7,
            max_tokens=1000,
        )

    async def _on_start(self) -> None:
        """LLMエージェント初期化。"""
        if not self.llm_config.api_key:
            raise ValueError("OPENAI_API_KEY is required")

        self._llm_agent = LLMAgent("LLMService", self.llm_config)
        await self._llm_agent.__aenter__()

    async def _on_stop(self) -> None:
        """LLMエージェント終了処理。"""
        if self._llm_agent:
            await self._llm_agent.__aexit__(None, None, None)
            self._llm_agent = None

    async def _health_check(self) -> bool:
        """LLMサービスのヘルスチェック。"""
        if not self._llm_agent:
            return False

        try:
            # 簡単なテストリクエスト
            test_task = Task(
                id="health_check",
                name="ヘルスチェック",
                data={
                    "messages": [{"role": "user", "content": "Hello"}],
                    "max_tokens": 10,
                },
            )

            result = await self._llm_agent.run_single_task(test_task)
            return result.error is None

        except Exception:
            return False

    async def _process_request(self, request: ServiceRequest) -> Any:
        """LLMリクエスト処理。"""
        if not self._llm_agent:
            raise RuntimeError("LLM agent is not initialized")

        operation = request.operation
        data = request.data

        if operation == "generate":
            # テキスト生成
            task = Task(
                id=request.request_id,
                name=data.get("name", "生成タスク"),
                data={
                    "messages": data.get("messages", []),
                    "temperature": data.get("temperature", self.llm_config.temperature),
                    "max_tokens": data.get("max_tokens", self.llm_config.max_tokens),
                },
            )

            result = await self._llm_agent.run_single_task(task)

            if result.error:
                raise Exception(f"LLM generation failed: {result.error}")

            return {
                "text": result.result,
                "task_id": result.id,
                "completed_at": result.completed_at.isoformat()
                if result.completed_at
                else None,
            }

        elif operation == "batch_generate":
            # バッチ生成
            tasks_data = data.get("tasks", [])
            tasks = [
                Task(
                    id=f"{request.request_id}_{i}",
                    name=task_data.get("name", f"バッチタスク{i + 1}"),
                    data=task_data.get("data", {}),
                )
                for i, task_data in enumerate(tasks_data)
            ]

            results = await self._llm_agent.run_tasks(tasks)

            return {
                "results": [
                    {
                        "task_id": task.id,
                        "text": task.result,
                        "error": str(task.error) if task.error else None,
                        "completed_at": task.completed_at.isoformat()
                        if task.completed_at
                        else None,
                    }
                    for task in results.values()
                ],
                "total": len(results),
                "successful": len([t for t in results.values() if t.error is None]),
            }

        else:
            raise ValueError(f"Unknown operation: {operation}")


class RAGAgentService(BaseService):
    """RAGエージェントのサービス実装。"""

    def __init__(
        self,
        name: str = "rag-agent-service",
        llm_config: Optional[LLMConfig] = None,
        **kwargs,
    ):
        super().__init__(
            name=name,
            description="検索拡張生成（RAG）を提供するサービス",
            version="1.0.0",
            tags=["rag", "search", "knowledge", "ai"],
            dependencies=["database"],
            **kwargs,
        )

        self.llm_config = llm_config or self._create_default_config()
        self._db_manager: Optional[DatabaseManager] = None
        self._rag_agent: Optional[SmartKnowledgeAgent] = None

    def _create_default_config(self) -> LLMConfig:
        """デフォルトのLLM設定を作成。"""
        return LLMConfig(
            api_url=os.getenv(
                "OPENAI_API_URL", "https://api.openai.com/v1/chat/completions"
            ),
            api_key=os.getenv("OPENAI_API_KEY", ""),
            model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
            temperature=0.7,
            max_tokens=1000,
        )

    async def _on_start(self) -> None:
        """RAGエージェント初期化。"""
        if not self.llm_config.api_key:
            raise ValueError("OPENAI_API_KEY is required")

        # データベースマネージャー初期化
        self._db_manager = DatabaseManager()
        await self._db_manager.connect()

        # RAGエージェント初期化
        self._rag_agent = SmartKnowledgeAgent(
            "RAGService", self.llm_config, self._db_manager
        )
        await self._rag_agent.__aenter__()

    async def _on_stop(self) -> None:
        """RAGエージェント終了処理。"""
        if self._rag_agent:
            await self._rag_agent.__aexit__(None, None, None)
            self._rag_agent = None

        if self._db_manager:
            await self._db_manager.disconnect()
            self._db_manager = None

    async def _health_check(self) -> bool:
        """RAGサービスのヘルスチェック。"""
        if not self._db_manager or not self._rag_agent:
            return False

        try:
            # データベース接続確認
            db_healthy = await self._db_manager.health_check()
            if not db_healthy:
                return False

            # 簡単なRAGテスト
            test_task = Task(
                id="health_check",
                name="ヘルスチェック",
                data={"question": "テスト質問"},
            )

            result = await self._rag_agent.run_single_task(test_task)
            return result.error is None

        except Exception:
            return False

    async def _process_request(self, request: ServiceRequest) -> Any:
        """RAGリクエスト処理。"""
        if not self._rag_agent:
            raise RuntimeError("RAG agent is not initialized")

        operation = request.operation
        data = request.data

        if operation == "question":
            # 単一質問処理
            question = data.get("question", "")
            if not question:
                raise ValueError("Question is required")

            task = Task(
                id=request.request_id, name="RAG質問", data={"question": question}
            )

            result = await self._rag_agent.run_single_task(task)

            if result.error:
                raise Exception(f"RAG processing failed: {result.error}")

            if not isinstance(result.result, AgentResponse):
                raise Exception("Invalid response type from RAG agent")

            response = result.result

            return {
                "answer": response.answer,
                "used_database": response.used_database,
                "decision_reasoning": response.decision_reasoning,
                "sources": [
                    {
                        "id": source.id,
                        "title": source.title,
                        "category": source.category,
                        "tags": source.tags,
                    }
                    for source in response.sources
                ],
                "metadata": {
                    "source_count": len(response.sources),
                    "processing_type": "database_enhanced"
                    if response.used_database
                    else "direct_llm",
                },
            }

        elif operation == "batch_questions":
            # 複数質問処理
            questions = data.get("questions", [])
            if not questions:
                raise ValueError("Questions list is required")

            tasks = [
                Task(
                    id=f"{request.request_id}_{i}",
                    name=f"RAG質問{i + 1}",
                    data={"question": question},
                )
                for i, question in enumerate(questions)
            ]

            results = await self._rag_agent.run_tasks(tasks)

            responses = []
            for task in results.values():
                if task.error:
                    responses.append(
                        {"question": None, "error": str(task.error), "success": False}
                    )
                else:
                    if not isinstance(task.result, AgentResponse):
                        responses.append(
                            {
                                "question": None,
                                "error": "Invalid response type",
                                "success": False,
                            }
                        )
                    else:
                        task_response = task.result
                        responses.append(
                            {
                                "question": None,  # 元の質問を追加する場合は別途管理が必要
                                "answer": task_response.answer,
                                "used_database": task_response.used_database,
                                "source_count": str(len(task_response.sources)),
                                "success": True,
                            }
                        )

            return {
                "responses": responses,
                "total": len(responses),
                "successful": len([r for r in responses if r.get("success", False)]),
                "database_usage_count": len(
                    [r for r in responses if r.get("used_database", False)]
                ),
            }

        elif operation == "search_knowledge":
            # ナレッジベース直接検索
            query = data.get("query", "")
            category = data.get("category")
            limit = data.get("limit", 5)

            if not query:
                raise ValueError("Search query is required")

            if not self._db_manager:
                raise RuntimeError("Database manager is not initialized")

            search_results = await self._db_manager.search_knowledge(
                query, category, limit
            )

            return {
                "query": query,
                "category": category,
                "results": [
                    {
                        "id": item.id,
                        "title": item.title,
                        "content": item.content[:200] + "..."
                        if len(item.content) > 200
                        else item.content,
                        "category": item.category,
                        "tags": item.tags,
                        "created_at": item.created_at.isoformat()
                        if item.created_at
                        else None,
                    }
                    for item in search_results
                ],
                "total_found": len(search_results),
            }

        else:
            raise ValueError(f"Unknown operation: {operation}")


class DatabaseService(BaseService):
    """データベースサービス実装。"""

    def __init__(self, name: str = "database-service", **kwargs):
        super().__init__(
            name=name,
            description="PostgreSQLデータベースへの接続とクエリ実行を提供",
            version="1.0.0",
            tags=["database", "postgresql", "storage"],
            **kwargs,
        )

        self._db_manager: Optional[DatabaseManager] = None

    async def _on_start(self) -> None:
        """データベース接続開始。"""
        self._db_manager = DatabaseManager()
        await self._db_manager.connect()

    async def _on_stop(self) -> None:
        """データベース接続終了。"""
        if self._db_manager:
            await self._db_manager.disconnect()
            self._db_manager = None

    async def _health_check(self) -> bool:
        """データベースヘルスチェック。"""
        if not self._db_manager:
            return False

        return await self._db_manager.health_check()

    async def _process_request(self, request: ServiceRequest) -> Any:
        """データベースリクエスト処理。"""
        if not self._db_manager:
            raise RuntimeError("Database manager is not initialized")

        operation = request.operation
        data = request.data

        if operation == "search":
            query = data.get("query", "")
            category = data.get("category")
            limit = data.get("limit", 10)

            results = await self._db_manager.search_knowledge(query, category, limit)

            return {
                "results": [
                    {
                        "id": item.id,
                        "title": item.title,
                        "content": item.content,
                        "category": item.category,
                        "tags": item.tags,
                    }
                    for item in results
                ]
            }

        elif operation == "get_categories":
            categories = await self._db_manager.get_all_categories()
            return {"categories": categories}

        elif operation == "get_by_category":
            category = data.get("category", "")
            limit = data.get("limit", 10)

            results = await self._db_manager.get_by_category(category, limit)

            return {
                "category": category,
                "results": [
                    {
                        "id": item.id,
                        "title": item.title,
                        "content": item.content,
                        "tags": item.tags,
                    }
                    for item in results
                ],
            }

        else:
            raise ValueError(f"Unknown operation: {operation}")
