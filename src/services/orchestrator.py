"""オーケストレーションサービス実装。"""

import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
import uuid

from .base import BaseService, ServiceRequest, ServiceResponse
from .registry import ServiceRegistry, ServiceRegistryEvent, RegistryEvent
from .agent_services import LLMAgentService, RAGAgentService, DatabaseService

logger = logging.getLogger(__name__)


class WorkflowStatus(Enum):
    """ワークフローの状態。"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class WorkflowStep:
    """ワークフローステップ定義。"""

    step_id: str
    service_name: str
    operation: str
    data: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)  # 依存するステップID
    timeout: float = 30.0
    retry_count: int = 0
    parallel: bool = True  # 並列実行可能かどうか


@dataclass
class WorkflowExecution:
    """ワークフロー実行情報。"""

    workflow_id: str
    steps: List[WorkflowStep]
    status: WorkflowStatus = WorkflowStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    results: Dict[str, ServiceResponse] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


class OrchestratorService(BaseService):
    """サービスオーケストレーター。"""

    def __init__(
        self,
        name: str = "orchestrator-service",
        registry: Optional[ServiceRegistry] = None,
        **kwargs,
    ):
        super().__init__(
            name=name,
            description="複数サービス間のワークフロー調整とオーケストレーション",
            version="1.0.0",
            tags=["orchestration", "workflow", "coordination"],
            **kwargs,
        )

        self.registry = registry or ServiceRegistry()
        self._workflows: Dict[str, WorkflowExecution] = {}
        self._running_workflows: Dict[str, asyncio.Task] = {}

        # 統計情報
        self._total_workflows = 0
        self._successful_workflows = 0
        self._failed_workflows = 0

    async def _on_start(self) -> None:
        """オーケストレーター開始。"""
        # レジストリ開始
        await self.registry.start()

        # イベントハンドラー登録
        self.registry.add_event_handler(self._handle_registry_event)

        logger.info("Orchestrator service started")

    async def _on_stop(self) -> None:
        """オーケストレーター停止。"""
        # 実行中ワークフロー停止
        for workflow_id, task in self._running_workflows.items():
            logger.info(f"Cancelling workflow: {workflow_id}")
            task.cancel()

        # 全タスク完了待機
        if self._running_workflows:
            await asyncio.gather(
                *self._running_workflows.values(), return_exceptions=True
            )

        # レジストリ停止
        await self.registry.stop()

        logger.info("Orchestrator service stopped")

    async def _health_check(self) -> bool:
        """オーケストレーターヘルスチェック。"""
        try:
            # レジストリの動作確認
            services = self.registry.get_running_services()
            return len(services) >= 0  # レジストリが動作していればOK
        except Exception:
            return False

    async def _process_request(self, request: ServiceRequest) -> Any:
        """オーケストレーターリクエスト処理。"""
        operation = request.operation
        data = request.data

        if operation == "execute_workflow":
            # ワークフロー実行
            steps_data = data.get("steps", [])
            if not steps_data:
                raise ValueError("Workflow steps are required")

            # ワークフローステップ構築
            steps = [
                WorkflowStep(
                    step_id=step.get("step_id", f"step_{i}"),
                    service_name=step.get("service_name", ""),
                    operation=step.get("operation", ""),
                    data=step.get("data", {}),
                    depends_on=step.get("depends_on", []),
                    timeout=step.get("timeout", 30.0),
                    retry_count=step.get("retry_count", 0),
                    parallel=step.get("parallel", True),
                )
                for i, step in enumerate(steps_data)
            ]

            # ワークフロー実行
            workflow_id = await self.execute_workflow(steps)

            return {
                "workflow_id": workflow_id,
                "status": "started",
                "steps_count": len(steps),
            }

        elif operation == "get_workflow_status":
            # ワークフロー状態取得
            workflow_id = data.get("workflow_id", "")
            workflow = self._workflows.get(workflow_id)

            if not workflow:
                raise ValueError(f"Workflow {workflow_id} not found")

            return {
                "workflow_id": workflow_id,
                "status": workflow.status.value,
                "created_at": workflow.created_at.isoformat(),
                "started_at": workflow.started_at.isoformat()
                if workflow.started_at
                else None,
                "completed_at": workflow.completed_at.isoformat()
                if workflow.completed_at
                else None,
                "steps_total": len(workflow.steps),
                "steps_completed": len(workflow.results),
                "errors": workflow.errors,
            }

        elif operation == "cancel_workflow":
            # ワークフローキャンセル
            workflow_id = data.get("workflow_id", "")
            success = await self.cancel_workflow(workflow_id)

            return {"workflow_id": workflow_id, "cancelled": success}

        elif operation == "get_services":
            # 登録済みサービス一覧
            services_info = await self.registry.get_all_service_info()

            return {
                "services": [
                    {
                        "service_id": info.service_id,
                        "name": info.name,
                        "description": info.description,
                        "status": info.status.value,
                        "tags": info.tags,
                        "dependencies": info.dependencies,
                        "metrics": {
                            "total_requests": info.metrics.total_requests,
                            "success_rate": info.metrics.success_rate,
                            "average_response_time": info.metrics.average_response_time,
                        },
                    }
                    for info in services_info
                ]
            }

        elif operation == "register_service":
            # サービス登録
            service_type = data.get("service_type", "")
            service_config = data.get("config", {})

            service = await self._create_service(service_type, service_config)
            if not service:
                raise ValueError(f"Unknown service type: {service_type}")

            success = await self.registry.register_service(service)

            return {
                "service_id": service.service_id,
                "service_name": service.name,
                "registered": success,
            }

        else:
            raise ValueError(f"Unknown operation: {operation}")

    async def execute_workflow(self, steps: List[WorkflowStep]) -> str:
        """ワークフロー実行。"""
        workflow_id = str(uuid.uuid4())

        workflow = WorkflowExecution(
            workflow_id=workflow_id, steps=steps, status=WorkflowStatus.PENDING
        )

        self._workflows[workflow_id] = workflow
        self._total_workflows += 1

        # ワークフロー実行タスク開始
        task = asyncio.create_task(self._execute_workflow_task(workflow))
        self._running_workflows[workflow_id] = task

        logger.info(f"Started workflow {workflow_id} with {len(steps)} steps")

        return workflow_id

    async def cancel_workflow(self, workflow_id: str) -> bool:
        """ワークフローキャンセル。"""
        if workflow_id not in self._running_workflows:
            return False

        task = self._running_workflows[workflow_id]
        task.cancel()

        # ワークフロー状態更新
        if workflow_id in self._workflows:
            workflow = self._workflows[workflow_id]
            workflow.status = WorkflowStatus.CANCELLED
            workflow.completed_at = datetime.now()

        logger.info(f"Cancelled workflow: {workflow_id}")
        return True

    async def get_workflow_result(
        self, workflow_id: str
    ) -> Optional[WorkflowExecution]:
        """ワークフロー結果取得。"""
        return self._workflows.get(workflow_id)

    async def _execute_workflow_task(self, workflow: WorkflowExecution) -> None:
        """ワークフロー実行タスク。"""
        workflow_id = workflow.workflow_id

        try:
            workflow.status = WorkflowStatus.RUNNING
            workflow.started_at = datetime.now()

            logger.info(f"Executing workflow {workflow_id}")

            # 依存関係解決とステップ実行
            await self._execute_workflow_steps(workflow)

            # 成功完了
            workflow.status = WorkflowStatus.COMPLETED
            workflow.completed_at = datetime.now()
            self._successful_workflows += 1

            logger.info(f"Workflow {workflow_id} completed successfully")

        except asyncio.CancelledError:
            workflow.status = WorkflowStatus.CANCELLED
            workflow.completed_at = datetime.now()
            logger.info(f"Workflow {workflow_id} was cancelled")

        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
            workflow.completed_at = datetime.now()
            workflow.errors.append(str(e))
            self._failed_workflows += 1

            logger.error(f"Workflow {workflow_id} failed: {e}")

        finally:
            # 実行中ワークフローから削除
            if workflow_id in self._running_workflows:
                del self._running_workflows[workflow_id]

    async def _execute_workflow_steps(self, workflow: WorkflowExecution) -> None:
        """ワークフローステップの依存関係を解決して実行。"""
        steps = workflow.steps
        completed_steps = set()
        pending_steps = {step.step_id: step for step in steps}

        while pending_steps:
            # 実行可能なステップを特定
            ready_steps = []
            for step_id, step in pending_steps.items():
                # 依存関係確認
                dependencies_met = all(
                    dep in completed_steps for dep in step.depends_on
                )
                if dependencies_met:
                    ready_steps.append(step)

            if not ready_steps:
                # デッドロック検出
                raise RuntimeError("Workflow deadlock detected: circular dependencies")

            # 並列実行可能なステップとシーケンシャルステップを分離
            parallel_steps = [step for step in ready_steps if step.parallel]
            sequential_steps = [step for step in ready_steps if not step.parallel]

            # 並列実行
            if parallel_steps:
                tasks = [
                    self._execute_single_step(workflow, step) for step in parallel_steps
                ]

                results = await asyncio.gather(*tasks, return_exceptions=True)

                for step, result in zip(parallel_steps, results):
                    if isinstance(result, Exception):
                        workflow.errors.append(f"Step {step.step_id} failed: {result}")
                        raise result

                    completed_steps.add(step.step_id)
                    del pending_steps[step.step_id]

            # シーケンシャル実行
            for step in sequential_steps:
                try:
                    await self._execute_single_step(workflow, step)
                    completed_steps.add(step.step_id)
                    del pending_steps[step.step_id]
                except Exception as e:
                    workflow.errors.append(f"Step {step.step_id} failed: {e}")
                    raise

    async def _execute_single_step(
        self, workflow: WorkflowExecution, step: WorkflowStep
    ) -> None:
        """単一ステップ実行。"""
        logger.info(f"Executing step {step.step_id} in workflow {workflow.workflow_id}")

        # サービス検索
        service = self.registry.find_service_by_name(step.service_name)
        if not service:
            raise RuntimeError(f"Service {step.service_name} not found")

        if not service.is_running:
            raise RuntimeError(f"Service {step.service_name} is not running")

        # リクエスト作成
        request = ServiceRequest(
            operation=step.operation, data=step.data, timeout=step.timeout
        )

        # リトライロジック
        retry_count = 0
        while retry_count <= step.retry_count:
            try:
                response = await service.process_request(request)

                if response.success:
                    workflow.results[step.step_id] = response
                    logger.info(f"Step {step.step_id} completed successfully")
                    return
                else:
                    raise RuntimeError(
                        f"Service request failed: {response.error_message}"
                    )

            except Exception as e:
                retry_count += 1
                if retry_count > step.retry_count:
                    logger.error(
                        f"Step {step.step_id} failed after {retry_count} retries: {e}"
                    )
                    raise
                else:
                    logger.warning(
                        f"Step {step.step_id} failed, retrying ({retry_count}/{step.retry_count}): {e}"
                    )
                    await asyncio.sleep(1.0 * retry_count)  # 指数バックオフ

    async def _create_service(
        self, service_type: str, config: Dict[str, Any]
    ) -> Optional[BaseService]:
        """サービスタイプから適切なサービスインスタンスを作成。"""
        if service_type == "llm":
            return LLMAgentService(**config)
        elif service_type == "rag":
            return RAGAgentService(**config)
        elif service_type == "database":
            return DatabaseService(**config)
        else:
            return None

    def _handle_registry_event(self, event: ServiceRegistryEvent) -> None:
        """レジストリイベント処理。"""
        logger.info(
            f"Registry event: {event.event_type.value} for service {event.service_name}"
        )

        if event.event_type == RegistryEvent.SERVICE_HEALTH_CHECK_FAILED:
            # ヘルスチェック失敗時の処理
            # 必要に応じて依存サービスの再起動や代替サービスへの切り替えを実装
            pass

    async def get_orchestrator_stats(self) -> Dict[str, Any]:
        """オーケストレーター統計情報取得。"""
        running_services = self.registry.get_running_services()

        return {
            "total_workflows": self._total_workflows,
            "successful_workflows": self._successful_workflows,
            "failed_workflows": self._failed_workflows,
            "success_rate": (self._successful_workflows / max(self._total_workflows, 1))
            * 100,
            "active_workflows": len(self._running_workflows),
            "registered_services": len(self.registry.get_all_services()),
            "running_services": len(running_services),
            "service_health": {
                service.name: service.status.value for service in running_services
            },
        }
