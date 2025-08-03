"""情報取得の必要性を判断する賢いエージェント。"""

from typing import List, Optional
from dataclasses import dataclass
import json

from .base import BaseAgent, Task
from .llm_agent import LLMAgent, LLMConfig
from .database import DatabaseManager, KnowledgeItem


@dataclass
class DecisionResult:
    """エージェントの判断結果。"""

    needs_database: bool
    search_queries: List[str]
    reasoning: str
    confidence: float


@dataclass
class AgentResponse:
    """エージェントの最終回答。"""

    answer: str
    sources: List[KnowledgeItem]
    used_database: bool
    decision_reasoning: str


class SmartKnowledgeAgent(BaseAgent):
    """データベース検索の必要性を判断する賢いエージェント。"""

    def __init__(
        self,
        name: str,
        llm_config: LLMConfig,
        db_manager: DatabaseManager,
        max_concurrent_tasks: int = 3,
    ):
        super().__init__(name, max_concurrent_tasks)
        self.llm_config = llm_config
        self.db_manager = db_manager
        self._llm_agent: Optional[LLMAgent] = None

    async def __aenter__(self) -> "SmartKnowledgeAgent":
        """非同期コンテキストマネージャの開始。"""
        self._llm_agent = LLMAgent("DecisionLLM", self.llm_config)
        await self._llm_agent.__aenter__()
        await self.db_manager.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """非同期コンテキストマネージャの終了。"""
        if self._llm_agent:
            await self._llm_agent.__aexit__(exc_type, exc_val, exc_tb)
        await self.db_manager.disconnect()

    async def process_task(self, task: Task) -> AgentResponse:
        """質問を処理してRAG回答を生成。"""
        question = task.data.get("question", "")

        if not question:
            raise ValueError("Question is required in task data")

        # ステップ1: データベース検索の必要性を判断
        decision = await self._decide_database_search(question)

        sources = []
        if decision.needs_database:
            # ステップ2: データベースから関連情報を取得
            sources = await self._fetch_relevant_knowledge(decision.search_queries)

        # ステップ3: 最終回答を生成
        answer = await self._generate_final_answer(question, sources, decision)

        return AgentResponse(
            answer=answer,
            sources=sources,
            used_database=decision.needs_database,
            decision_reasoning=decision.reasoning,
        )

    async def _decide_database_search(self, question: str) -> DecisionResult:
        """データベース検索の必要性を判断。"""
        decision_prompt = f"""
あなたは質問分析の専門家です。以下の質問について、Claude Codeナレッジベースから情報を取得する必要があるかを判断してください。

質問: {question}

ナレッジベースには以下のカテゴリの情報があります：
- 基本情報: Claude Codeの概要と特徴
- セットアップ: インストールと初期設定
- 機能: 各種機能の詳細説明
- 高度な機能: TaskGroupなど高度な機能
- プロジェクト管理: Git統合、依存関係管理
- デバッグ: エラーハンドリングとトラブルシューティング
- 言語サポート: 対応プログラミング言語
- 最適化: パフォーマンスと品質向上
- トラブルシューティング: 問題解決

以下のJSON形式で回答してください：
{{
    "needs_database": true/false,
    "search_queries": ["検索クエリ1", "検索クエリ2"],
    "reasoning": "判断理由の説明",
    "confidence": 0.0-1.0
}}

判断基準：
- Claude Codeに関する具体的な質問 → データベース検索が必要
- 一般的なプログラミング質問 → データベース検索不要
- あいさつや雑談 → データベース検索不要
"""

        task = Task(
            id="decision",
            name="決定タスク",
            data={
                "messages": [{"role": "user", "content": decision_prompt}],
                "temperature": 0.2,
            },
        )

        if not self._llm_agent:
            raise RuntimeError("LLM agent is not initialized")

        result = await self._llm_agent.run_single_task(task)

        try:
            result_text = result.result
            if result_text is None:
                raise ValueError("LLM result is None")
            decision_data = json.loads(result_text)
            return DecisionResult(
                needs_database=decision_data.get("needs_database", False),
                search_queries=decision_data.get("search_queries", []),
                reasoning=decision_data.get("reasoning", ""),
                confidence=decision_data.get("confidence", 0.0),
            )
        except json.JSONDecodeError:
            # JSONパースに失敗した場合のフォールバック
            claude_keywords = [
                "claude",
                "code",
                "claude-code",
                "インストール",
                "エラー",
                "機能",
            ]
            needs_database = any(
                keyword in question.lower() for keyword in claude_keywords
            )

            return DecisionResult(
                needs_database=needs_database,
                search_queries=[question] if needs_database else [],
                reasoning="JSON parse failed, using keyword-based fallback",
                confidence=0.5,
            )

    async def _fetch_relevant_knowledge(
        self, search_queries: List[str]
    ) -> List[KnowledgeItem]:
        """検索クエリに基づいて関連ナレッジを取得。"""
        all_results = []
        seen_ids = set()

        for query in search_queries:
            results = await self.db_manager.search_knowledge(query, limit=3)
            for item in results:
                if item.id not in seen_ids:
                    all_results.append(item)
                    seen_ids.add(item.id)

        # 関連度順にソート（最大5件）
        return all_results[:5]

    async def _generate_final_answer(
        self, question: str, sources: List[KnowledgeItem], decision: DecisionResult
    ) -> str:
        """ナレッジソースを使用して最終回答を生成。"""
        if sources:
            # ナレッジベースの情報を使用
            context = "\n\n".join(
                [f"【{source.title}】\n{source.content}" for source in sources]
            )

            prompt = f"""
以下の質問に対して、提供されたナレッジベースの情報を参考に回答してください。

質問: {question}

参考情報:
{context}

回答の指針：
- 正確で実用的な情報を提供
- ナレッジベースの情報を主に使用
- 足りない部分は一般的な知識で補完
- 日本語で分かりやすく回答
- 具体的な手順やコマンドがあれば含める
"""
        else:
            # ナレッジベースを使わない通常回答
            prompt = f"""
以下の質問に回答してください。Claude Codeに関する専門的な質問でない場合は、一般的な知識で回答してください。

質問: {question}

回答の指針：
- 親切で正確な回答を提供
- 日本語で分かりやすく説明
- 実用的なアドバイスを含める
"""

        task = Task(
            id="answer",
            name="回答生成",
            data={
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
            },
        )

        if not self._llm_agent:
            raise RuntimeError("LLM agent is not initialized")

        result = await self._llm_agent.run_single_task(task)
        return result.result or ""


class BatchKnowledgeAgent(BaseAgent):
    """複数質問を並行処理するバッチエージェント。"""

    def __init__(self, smart_agent: SmartKnowledgeAgent, max_concurrent_tasks: int = 5):
        super().__init__("BatchKnowledgeAgent", max_concurrent_tasks)
        self.smart_agent = smart_agent

    async def process_task(self, task: Task) -> AgentResponse:
        """SmartKnowledgeAgentに処理を委譲。"""
        return await self.smart_agent.process_task(task)

    async def process_questions(self, questions: List[str]) -> List[AgentResponse]:
        """複数の質問を並行処理。"""
        tasks = [
            Task(id=f"q_{i}", name=f"質問{i + 1}", data={"question": question})
            for i, question in enumerate(questions)
        ]

        results = await self.run_tasks(tasks)

        # 結果をタスクIDでソートして返す
        responses = []
        for i in range(len(questions)):
            task_result = results[f"q_{i}"]
            if task_result.result is not None:
                responses.append(task_result.result)
        return responses
