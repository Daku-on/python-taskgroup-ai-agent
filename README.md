# Python TaskGroup AI Agent

## 何をするプロジェクトか / What This Project Does

このプロジェクトは、Python 3.11以降のasyncio TaskGroupを活用して、複数のAIタスクを効率的に並行実行するためのフレームワークです。特にLLM API（OpenAI GPT、Claude、Geminiなど）への複数リクエストを同時に処理し、処理時間を大幅に短縮できます。

例えば：
- 10個のテキスト生成タスクを順次実行すると30秒かかる処理を、並行実行により8秒に短縮
- 異なる種類のAI処理（翻訳、要約、分析）を複数エージェントで同時実行
- 大量のデータ処理やバッチ処理を効率化

This project is a framework for efficiently executing multiple AI tasks concurrently using Python 3.11+ asyncio TaskGroup. It's particularly designed for processing multiple LLM API requests (OpenAI GPT, Claude, Gemini, etc.) simultaneously, significantly reducing processing time.

For example:
- Reduce 30-second sequential execution of 10 text generation tasks to 8 seconds with concurrent execution
- Execute different types of AI processing (translation, summarization, analysis) simultaneously with multiple agents
- Optimize large-scale data processing and batch operations

## 特徴 / Features

- 🚀 **並行タスク実行 / Concurrent Task Execution**: Python 3.11+ TaskGroupを基盤とした効率的な並列処理 / Built on Python 3.11+ TaskGroup for efficient parallel processing
- 🤖 **柔軟なエージェント設計 / Flexible Agent Architecture**: カスタムエージェント実装のための拡張可能な基底クラス / Extensible base classes for custom agent implementations
- 🔄 **マルチエージェント協調 / Multi-Agent Orchestration**: 複雑なパイプラインでの複数エージェント連携 / Coordinate multiple agents in complex pipelines
- ⚡ **非同期ファースト設計 / Async-First Design**: 最適なパフォーマンスのための完全async/awaitサポート / Full async/await support for optimal performance
- 🛡️ **組み込みエラーハンドリング / Built-in Error Handling**: TaskGroupの例外管理による堅牢なエラー処理 / Robust error handling with TaskGroup's exception management
- 📊 **タスク追跡 / Task Tracking**: タスクステータス、結果、実行時間の監視 / Monitor task status, results, and execution times

## 必要環境 / Requirements

- Python 3.11 or higher
- uv (for dependency management)

## インストール / Installation

```bash
# リポジトリをクローン / Clone the repository
git clone https://github.com/Daku-on/python-taskgroup-ai-agent.git
cd python-taskgroup-ai-agent

# 依存関係をインストール / Install dependencies
uv sync

# 開発用依存関係も含める場合 / For development dependencies
uv sync --group dev

# 環境変数を設定 / Set up environment variables
cp .env.example .env
# .envファイルを編集してAPIキーを追加 / Edit .env file and add your API keys
```

## Quick Start

### Basic Agent Example

```python
import asyncio
from src.agent.base import BaseAgent, Task

class MyAgent(BaseAgent):
    async def process_task(self, task: Task):
        # Your task processing logic here
        result = await some_async_operation(task.data)
        return result

# Use the agent
async def main():
    agent = MyAgent(name="MyAgent", max_concurrent_tasks=10)
    
    tasks = [
        Task(id="1", name="Task 1", data={"prompt": "Hello"}),
        Task(id="2", name="Task 2", data={"prompt": "World"}),
    ]
    
    results = await agent.run_tasks(tasks)
    print(results)

asyncio.run(main())
```

### LLM Agent Example

```python
from src.agent.llm_agent import LLMAgent, LLMConfig

# Configure your LLM
config = LLMConfig(
    api_url="https://api.openai.com/v1/chat/completions",
    api_key="your-api-key",
    model="gpt-3.5-turbo"
)

# Create agent
async with LLMAgent("GPT-Agent", config) as agent:
    task = Task(
        id="1",
        name="Generate Story",
        data={"prompt": "Write a short story about AI"}
    )
    
    result = await agent.run_single_task(task)
    print(result.result)
```

### Multi-Agent Pipeline

```python
from src.agent.llm_agent import MultiAgentOrchestrator

orchestrator = MultiAgentOrchestrator()
orchestrator.register_agent(agent1)
orchestrator.register_agent(agent2)

pipeline = [
    {
        "agent": "agent1",
        "tasks": [{"id": "1", "name": "Analyze", "data": {...}}]
    },
    {
        "agent": "agent2", 
        "tasks": [{"id": "2", "name": "Generate", "data": {...}}]
    }
]

results = await orchestrator.run_pipeline(pipeline)
```

## Architecture

The framework is built around three core concepts:

1. **Tasks**: Represent units of work with unique IDs, names, and data payloads
2. **Agents**: Process tasks asynchronously with configurable concurrency limits
3. **TaskGroups**: Python 3.11+ feature for structured concurrency and error handling

## Examples

Check the `examples/` directory for more detailed examples:
- `simple_agent.py`: Basic agent implementation with simulated tasks
- `openai_agent.py`: Real OpenAI API integration example
- `rag_agent.py`: **RAG (Retrieval-Augmented Generation) with PostgreSQL knowledge base**

### 🚀 Quick Start: RAG Agent Demo

**一発で全部セットアップ & デモ実行：**
```bash
# 自動セットアップ & RAGデモ実行
uv run python scripts/start_demo.py
```

**手動セットアップ:**
```bash
# 1. データベース起動
docker-compose up -d

# 2. ナレッジベース作成
uv run python database/setup_knowledge.py

# 3. RAGデモ実行
uv run python examples/rag_agent.py
```

### 🤖 RAG Agent Features / RAGエージェント機能

The RAG agent demonstrates intelligent information retrieval:

RAGエージェントは賢い情報検索を実演します：

- **🧠 Smart Decision Making / 賢い判断**: Automatically decides whether to fetch data from knowledge base / ナレッジベースからデータを取得するかを自動判断
- **📚 Knowledge Base Search / ナレッジベース検索**: PostgreSQL full-text search with Claude Code documentation / Claude Codeドキュメントを含むPostgreSQL全文検索
- **⚡ Concurrent Processing / 並行処理**: Multiple questions processed simultaneously using TaskGroup / TaskGroupを使用した複数質問の同時処理
- **🎯 Context-Aware Responses / 文脈を理解した回答**: Combines retrieved knowledge with LLM capabilities / 検索された知識とLLM機能を組み合わせ

**Example Questions / 質問例:**
- "Claude Codeをインストールする方法は？" → Uses knowledge base / ナレッジベース使用
- "今日の天気は？" → Direct LLM response / LLM直接回答  
- "TaskGroupの機能について教えて" → Uses knowledge base / ナレッジベース使用

### 🎭 Service Orchestration / サービスオーケストレーション

**Advanced service-based architecture with workflow orchestration:**

**ワークフローオーケストレーションを持つ高度なサービスベースアーキテクチャ:**

```bash
# オーケストレーションデモ実行 / Run orchestration demo
uv run python examples/orchestrator_demo.py

# インタラクティブダッシュボード / Interactive dashboard
uv run python examples/service_dashboard.py
```

**🏗️ Service Architecture Features / サービスアーキテクチャ機能:**

- **🔧 Service Registry / サービス登録**: Automatic service discovery and health monitoring / 自動サービス発見とヘルス監視
- **🎭 Orchestration Engine / オーケストレーションエンジン**: Workflow coordination with dependency resolution / 依存関係解決を持つワークフロー調整
- **⚡ Parallel & Sequential Execution / 並列・直列実行**: Mixed workflow patterns with TaskGroup / TaskGroupを使った混在ワークフローパターン
- **🔄 Auto Retry & Error Handling / 自動リトライ・エラーハンドリング**: Robust failure recovery mechanisms / 堅牢な障害回復メカニズム
- **📊 Real-time Monitoring / リアルタイム監視**: Service metrics and workflow tracking / サービスメトリクスとワークフロー追跡
- **🎛️ Management Dashboard / 管理ダッシュボード**: Interactive service management interface / インタラクティブサービス管理インターフェース

**Workflow Example / ワークフロー例:**
```python
workflow_steps = [
    {
        "step_id": "data_fetch",
        "service_name": "database-service", 
        "operation": "search",
        "depends_on": [],
        "parallel": True
    },
    {
        "step_id": "ai_analysis",
        "service_name": "rag-service",
        "operation": "question", 
        "depends_on": ["data_fetch"],
        "parallel": False
    }
]
```

## 開発 / Development

```bash
# テスト実行 / Run tests
uv run pytest tests/

# コードフォーマット / Code formatting
uv run ruff format .

# リンティング / Linting
uv run ruff check .

# 型チェック / Type checking
uv run mypy src/

# 全品質チェック一括実行 / Run all quality checks
uv run pytest tests/ && uv run ruff check . && uv run ruff format --check . && uv run mypy src/
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 日本語要約

Python 3.11以降のTaskGroupを活用したAIエージェントフレームワーク。複数のAI/LLM APIコールを効率的に並行処理するための設計。

主な特徴：
- TaskGroupによる並行タスク実行
- 拡張可能なエージェントアーキテクチャ
- マルチエージェントオーケストレーション
- 完全な非同期サポート
- 堅牢なエラーハンドリング

基本的な使い方は、BaseAgentを継承してprocess_taskメソッドを実装し、TaskGroupで複数タスクを並行実行する仕組み。