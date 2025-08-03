"""asyncio TaskGroupを使用した基本エージェント実装。"""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class Task:
    """エージェント用の単一タスクを表現。"""

    id: str
    name: str
    data: Dict[str, Any]
    created_at: datetime = datetime.now()
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[Exception] = None


class BaseAgent(ABC):
    """TaskGroupを使用した並行実行のためのAIエージェント基底クラス。"""

    def __init__(self, name: str, max_concurrent_tasks: int = 10):
        self.name = name
        self.max_concurrent_tasks = max_concurrent_tasks
        self._semaphore = asyncio.Semaphore(max_concurrent_tasks)
        self._task_results: Dict[str, Task] = {}

    @abstractmethod
    async def process_task(self, task: Task) -> Any:
        """単一タスクを処理。サブクラスで実装する必要がある。"""
        pass

    async def _execute_task(self, task: Task) -> None:
        """セマフォ制御で単一タスクを実行。"""
        async with self._semaphore:
            try:
                logger.info(f"Agent {self.name} starting task {task.id}: {task.name}")
                result = await self.process_task(task)
                task.result = result
                task.completed_at = datetime.now()
                logger.info(f"Agent {self.name} completed task {task.id}")
            except Exception as e:
                logger.error(f"Agent {self.name} failed task {task.id}: {e}")
                task.error = e
                task.completed_at = datetime.now()
            finally:
                self._task_results[task.id] = task

    async def run_tasks(self, tasks: List[Task]) -> Dict[str, Task]:
        """TaskGroupを使用して複数タスクを並行実行。"""
        self._task_results.clear()

        async with asyncio.TaskGroup() as tg:
            for task in tasks:
                tg.create_task(self._execute_task(task))

        return self._task_results

    async def run_single_task(self, task: Task) -> Task:
        """単一タスクを実行。"""
        await self._execute_task(task)
        return self._task_results[task.id]
