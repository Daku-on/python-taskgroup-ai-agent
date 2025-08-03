"""サービス登録・発見機能。"""

import asyncio
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
import logging
from enum import Enum

from .base import BaseService, ServiceInfo

logger = logging.getLogger(__name__)


class RegistryEvent(Enum):
    """レジストリイベントタイプ。"""

    SERVICE_REGISTERED = "service_registered"
    SERVICE_UNREGISTERED = "service_unregistered"
    SERVICE_STATUS_CHANGED = "service_status_changed"
    SERVICE_HEALTH_CHECK_FAILED = "service_health_check_failed"


@dataclass
class ServiceRegistryEvent:
    """サービスレジストリイベント。"""

    event_type: RegistryEvent
    service_id: str
    service_name: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


EventHandler = Callable[[ServiceRegistryEvent], None]


class ServiceRegistry:
    """サービス登録・発見レジストリ。"""

    def __init__(
        self, health_check_interval: float = 30.0, stale_service_timeout: float = 300.0
    ):
        self._services: Dict[str, BaseService] = {}
        self._service_info_cache: Dict[str, ServiceInfo] = {}
        self._event_handlers: List[EventHandler] = []

        # 設定
        self.health_check_interval = health_check_interval
        self.stale_service_timeout = stale_service_timeout

        # ヘルスチェックタスク
        self._health_check_task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self) -> None:
        """レジストリ開始。"""
        if self._running:
            return

        logger.info("Starting service registry")
        self._running = True

        # ヘルスチェックタスクを開始
        self._health_check_task = asyncio.create_task(self._health_check_loop())

    async def stop(self) -> None:
        """レジストリ停止。"""
        if not self._running:
            return

        logger.info("Stopping service registry")
        self._running = False

        # ヘルスチェックタスク停止
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass

        # 全サービス停止
        for service in self._services.values():
            if service.is_running:
                await service.stop()

        self._services.clear()
        self._service_info_cache.clear()

    async def register_service(self, service: BaseService) -> bool:
        """サービス登録。"""
        service_id = service.service_id

        if service_id in self._services:
            logger.warning(
                f"Service {service.name} ({service_id}) is already registered"
            )
            return False

        try:
            # サービス開始
            if not service.is_running:
                success = await service.start()
                if not success:
                    logger.error(f"Failed to start service {service.name}")
                    return False

            # 登録
            self._services[service_id] = service
            self._service_info_cache[service_id] = await service.get_info()

            # イベント発火
            await self._emit_event(
                ServiceRegistryEvent(
                    event_type=RegistryEvent.SERVICE_REGISTERED,
                    service_id=service_id,
                    service_name=service.name,
                )
            )

            logger.info(f"Service registered: {service.name} ({service_id})")
            return True

        except Exception as e:
            logger.error(f"Failed to register service {service.name}: {e}")
            return False

    async def unregister_service(self, service_id: str) -> bool:
        """サービス登録解除。"""
        if service_id not in self._services:
            logger.warning(f"Service {service_id} is not registered")
            return False

        try:
            service = self._services[service_id]
            service_name = service.name

            # サービス停止
            if service.is_running:
                await service.stop()

            # 登録解除
            del self._services[service_id]
            del self._service_info_cache[service_id]

            # イベント発火
            await self._emit_event(
                ServiceRegistryEvent(
                    event_type=RegistryEvent.SERVICE_UNREGISTERED,
                    service_id=service_id,
                    service_name=service_name,
                )
            )

            logger.info(f"Service unregistered: {service_name} ({service_id})")
            return True

        except Exception as e:
            logger.error(f"Failed to unregister service {service_id}: {e}")
            return False

    def get_service(self, service_id: str) -> Optional[BaseService]:
        """サービスIDでサービス取得。"""
        return self._services.get(service_id)

    def find_service_by_name(self, name: str) -> Optional[BaseService]:
        """サービス名でサービス検索。"""
        for service in self._services.values():
            if service.name == name:
                return service
        return None

    def find_services_by_tag(self, tag: str) -> List[BaseService]:
        """タグでサービス検索。"""
        matching_services = []
        for service in self._services.values():
            if tag in service.service_info.tags:
                matching_services.append(service)
        return matching_services

    def get_all_services(self) -> List[BaseService]:
        """全サービス一覧取得。"""
        return list(self._services.values())

    def get_running_services(self) -> List[BaseService]:
        """実行中サービス一覧取得。"""
        return [service for service in self._services.values() if service.is_running]

    async def get_service_info(self, service_id: str) -> Optional[ServiceInfo]:
        """サービス情報取得。"""
        service = self._services.get(service_id)
        if not service:
            return None

        # 最新情報を取得してキャッシュ更新
        info = await service.get_info()
        self._service_info_cache[service_id] = info
        return info

    async def get_all_service_info(self) -> List[ServiceInfo]:
        """全サービス情報一覧取得。"""
        info_list = []
        for service_id, service in self._services.items():
            try:
                info = await service.get_info()
                self._service_info_cache[service_id] = info
                info_list.append(info)
            except Exception as e:
                logger.error(f"Failed to get info for service {service_id}: {e}")

        return info_list

    def add_event_handler(self, handler: EventHandler) -> None:
        """イベントハンドラー追加。"""
        self._event_handlers.append(handler)

    def remove_event_handler(self, handler: EventHandler) -> None:
        """イベントハンドラー削除。"""
        if handler in self._event_handlers:
            self._event_handlers.remove(handler)

    async def _emit_event(self, event: ServiceRegistryEvent) -> None:
        """イベント発火。"""
        for handler in self._event_handlers:
            try:
                # 非同期ハンドラーの場合
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Event handler error: {e}")

    async def _health_check_loop(self) -> None:
        """定期ヘルスチェックループ。"""
        while self._running:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check loop error: {e}")
                await asyncio.sleep(5.0)  # エラー時は短いインターバル

    async def _perform_health_checks(self) -> None:
        """全サービスのヘルスチェック実行。"""
        check_tasks = []

        for service_id, service in self._services.items():
            if service.is_running:
                task = asyncio.create_task(
                    self._check_service_health(service_id, service)
                )
                check_tasks.append(task)

        if check_tasks:
            await asyncio.gather(*check_tasks, return_exceptions=True)

    async def _check_service_health(
        self, service_id: str, service: BaseService
    ) -> None:
        """個別サービスのヘルスチェック。"""
        try:
            is_healthy = await service.health_check()

            if not is_healthy:
                # ヘルスチェック失敗イベント
                await self._emit_event(
                    ServiceRegistryEvent(
                        event_type=RegistryEvent.SERVICE_HEALTH_CHECK_FAILED,
                        service_id=service_id,
                        service_name=service.name,
                        metadata={"health_status": "failed"},
                    )
                )

                logger.warning(f"Health check failed for service: {service.name}")

            # サービス情報キャッシュ更新
            self._service_info_cache[service_id] = await service.get_info()

        except Exception as e:
            logger.error(f"Health check error for service {service_id}: {e}")

            await self._emit_event(
                ServiceRegistryEvent(
                    event_type=RegistryEvent.SERVICE_HEALTH_CHECK_FAILED,
                    service_id=service_id,
                    service_name=service.name,
                    metadata={"error": str(e)},
                )
            )

    async def get_service_dependencies(self, service_id: str) -> List[str]:
        """サービスの依存関係取得。"""
        service = self._services.get(service_id)
        if not service:
            return []

        return service.service_info.dependencies

    async def validate_dependencies(self, service_id: str) -> bool:
        """サービス依存関係の検証。"""
        dependencies = await self.get_service_dependencies(service_id)

        for dep_name in dependencies:
            dep_service = self.find_service_by_name(dep_name)
            if not dep_service or not dep_service.is_running:
                logger.warning(
                    f"Dependency {dep_name} not available for service {service_id}"
                )
                return False

        return True
