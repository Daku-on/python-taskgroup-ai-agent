"""サービス基底クラスとインターフェース定義。"""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
import uuid

logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """サービスの状態。"""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"
    MAINTENANCE = "maintenance"


@dataclass
class ServiceMetrics:
    """サービスのメトリクス情報。"""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    last_request_time: Optional[datetime] = None
    uptime_seconds: float = 0.0
    memory_usage_mb: float = 0.0

    @property
    def success_rate(self) -> float:
        """成功率を計算。"""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100

    @property
    def error_rate(self) -> float:
        """エラー率を計算。"""
        return 100.0 - self.success_rate


@dataclass
class ServiceInfo:
    """サービス情報。"""

    service_id: str
    name: str
    description: str
    version: str
    status: ServiceStatus
    created_at: datetime
    last_health_check: Optional[datetime] = None
    metrics: ServiceMetrics = field(default_factory=ServiceMetrics)
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    configuration: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ServiceRequest:
    """サービスリクエスト。"""

    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    operation: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    timeout: float = 30.0
    priority: int = 1  # 1=高, 2=中, 3=低
    created_at: datetime = field(default_factory=datetime.now)
    correlation_id: Optional[str] = None


@dataclass
class ServiceResponse:
    """サービスレスポンス。"""

    request_id: str
    success: bool
    data: Any = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    execution_time: float = 0.0
    completed_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseService(ABC):
    """すべてのサービスの基底クラス。"""

    def __init__(
        self,
        name: str,
        description: str = "",
        version: str = "1.0.0",
        tags: Optional[List[str]] = None,
        dependencies: Optional[List[str]] = None,
        configuration: Optional[Dict[str, Any]] = None,
    ):
        self.service_info = ServiceInfo(
            service_id=str(uuid.uuid4()),
            name=name,
            description=description,
            version=version,
            status=ServiceStatus.STOPPED,
            created_at=datetime.now(),
            tags=tags or [],
            dependencies=dependencies or [],
            configuration=configuration or {},
        )

        self._start_time: Optional[datetime] = None
        self._request_times: List[float] = []
        self._lock = asyncio.Lock()

        # 設定
        self.max_concurrent_requests = (
            configuration.get("max_concurrent_requests", 10) if configuration else 10
        )
        self.request_timeout = (
            configuration.get("request_timeout", 30.0) if configuration else 30.0
        )

        # 並行制御
        self._semaphore = asyncio.Semaphore(self.max_concurrent_requests)

    @property
    def service_id(self) -> str:
        """サービスID取得。"""
        return self.service_info.service_id

    @property
    def name(self) -> str:
        """サービス名取得。"""
        return self.service_info.name

    @property
    def status(self) -> ServiceStatus:
        """現在のステータス取得。"""
        return self.service_info.status

    @property
    def is_running(self) -> bool:
        """実行中かどうか確認。"""
        return self.status == ServiceStatus.RUNNING

    async def start(self) -> bool:
        """サービスを開始。"""
        async with self._lock:
            if self.status != ServiceStatus.STOPPED:
                logger.warning(f"Service {self.name} is already running or starting")
                return False

            try:
                logger.info(f"Starting service: {self.name}")
                self.service_info.status = ServiceStatus.STARTING

                # 実装固有の開始処理
                await self._on_start()

                self.service_info.status = ServiceStatus.RUNNING
                self._start_time = datetime.now()

                logger.info(f"Service {self.name} started successfully")
                return True

            except Exception as e:
                logger.error(f"Failed to start service {self.name}: {e}")
                self.service_info.status = ServiceStatus.ERROR
                return False

    async def stop(self) -> bool:
        """サービスを停止。"""
        async with self._lock:
            if self.status == ServiceStatus.STOPPED:
                logger.warning(f"Service {self.name} is already stopped")
                return True

            try:
                logger.info(f"Stopping service: {self.name}")
                self.service_info.status = ServiceStatus.STOPPING

                # 実装固有の停止処理
                await self._on_stop()

                self.service_info.status = ServiceStatus.STOPPED
                self._start_time = None

                logger.info(f"Service {self.name} stopped successfully")
                return True

            except Exception as e:
                logger.error(f"Failed to stop service {self.name}: {e}")
                self.service_info.status = ServiceStatus.ERROR
                return False

    async def restart(self) -> bool:
        """サービスを再起動。"""
        logger.info(f"Restarting service: {self.name}")

        stop_success = await self.stop()
        if not stop_success:
            return False

        # 少し待機
        await asyncio.sleep(1.0)

        return await self.start()

    async def health_check(self) -> bool:
        """ヘルスチェック実行。"""
        try:
            is_healthy = await self._health_check()
            self.service_info.last_health_check = datetime.now()

            if not is_healthy and self.status == ServiceStatus.RUNNING:
                self.service_info.status = ServiceStatus.ERROR
                logger.error(f"Health check failed for service: {self.name}")

            return is_healthy

        except Exception as e:
            logger.error(f"Health check error for service {self.name}: {e}")
            self.service_info.status = ServiceStatus.ERROR
            return False

    async def process_request(self, request: ServiceRequest) -> ServiceResponse:
        """リクエストを処理。"""
        start_time = datetime.now()

        # 並行制御
        async with self._semaphore:
            try:
                # タイムアウト設定
                timeout = min(request.timeout, self.request_timeout)

                # リクエスト処理
                result = await asyncio.wait_for(
                    self._process_request(request), timeout=timeout
                )

                # 成功レスポンス
                execution_time = (datetime.now() - start_time).total_seconds()
                await self._update_metrics(True, execution_time)

                return ServiceResponse(
                    request_id=request.request_id,
                    success=True,
                    data=result,
                    execution_time=execution_time,
                )

            except asyncio.TimeoutError:
                execution_time = (datetime.now() - start_time).total_seconds()
                await self._update_metrics(False, execution_time)

                return ServiceResponse(
                    request_id=request.request_id,
                    success=False,
                    error_message="Request timeout",
                    error_code="TIMEOUT",
                    execution_time=execution_time,
                )

            except Exception as e:
                execution_time = (datetime.now() - start_time).total_seconds()
                await self._update_metrics(False, execution_time)

                return ServiceResponse(
                    request_id=request.request_id,
                    success=False,
                    error_message=str(e),
                    error_code="INTERNAL_ERROR",
                    execution_time=execution_time,
                )

    async def get_info(self) -> ServiceInfo:
        """サービス情報を取得。"""
        # アップタイム更新
        if self._start_time and self.status == ServiceStatus.RUNNING:
            self.service_info.metrics.uptime_seconds = (
                datetime.now() - self._start_time
            ).total_seconds()

        return self.service_info

    async def _update_metrics(self, success: bool, execution_time: float) -> None:
        """メトリクス更新。"""
        metrics = self.service_info.metrics

        metrics.total_requests += 1
        metrics.last_request_time = datetime.now()

        if success:
            metrics.successful_requests += 1
        else:
            metrics.failed_requests += 1

        # 平均レスポンス時間更新（移動平均）
        self._request_times.append(execution_time)
        if len(self._request_times) > 100:  # 最新100件のみ保持
            self._request_times.pop(0)

        metrics.average_response_time = sum(self._request_times) / len(
            self._request_times
        )

    # 抽象メソッド（サブクラスで実装）
    @abstractmethod
    async def _on_start(self) -> None:
        """サービス開始時の処理。"""
        pass

    @abstractmethod
    async def _on_stop(self) -> None:
        """サービス停止時の処理。"""
        pass

    @abstractmethod
    async def _health_check(self) -> bool:
        """ヘルスチェック処理。"""
        pass

    @abstractmethod
    async def _process_request(self, request: ServiceRequest) -> Any:
        """リクエスト処理の実装。"""
        pass
