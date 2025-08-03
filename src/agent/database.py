"""データベース接続とモデル定義。"""

import os
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime
import asyncpg
from dotenv import load_dotenv

load_dotenv()


@dataclass
class KnowledgeItem:
    """ナレッジベースのアイテム。"""

    id: Optional[int] = None
    title: str = ""
    content: str = ""
    category: str = ""
    tags: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        if self.tags is None:
            self.tags = []


class DatabaseManager:
    """データベース接続とクエリ管理。"""

    def __init__(self) -> None:
        self.database_url = os.getenv("DATABASE_URL")
        self._pool: Optional[asyncpg.Pool] = None

    async def __aenter__(self) -> "DatabaseManager":
        """非同期コンテキストマネージャの開始。"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """非同期コンテキストマネージャの終了。"""
        await self.disconnect()

    async def connect(self) -> None:
        """データベースプールを作成。"""
        if not self._pool:
            self._pool = await asyncpg.create_pool(
                self.database_url, min_size=1, max_size=10, command_timeout=60
            )

    async def disconnect(self) -> None:
        """データベースプールを閉じる。"""
        if self._pool:
            await self._pool.close()
            self._pool = None

    async def insert_knowledge(self, item: KnowledgeItem) -> int:
        """ナレッジアイテムを挿入。"""
        if not self._pool:
            await self.connect()

        if not self._pool:
            raise RuntimeError("Database pool is not available")

        query = """
        INSERT INTO knowledge_base (title, content, category, tags)
        VALUES ($1, $2, $3, $4)
        RETURNING id
        """

        async with self._pool.acquire() as conn:
            result = await conn.fetchval(
                query, item.title, item.content, item.category, item.tags or []
            )
            return result

    async def search_knowledge(
        self, query: str, category: Optional[str] = None, limit: int = 5
    ) -> List[KnowledgeItem]:
        """ナレッジベースから検索。"""
        if not self._pool:
            await self.connect()

        # 全文検索クエリ構築
        search_query = """
        SELECT id, title, content, category, tags, created_at, updated_at,
               ts_rank(to_tsvector('english', title || ' ' || content), 
                      plainto_tsquery('english', $1)) as rank
        FROM knowledge_base
        WHERE to_tsvector('english', title || ' ' || content) @@ plainto_tsquery('english', $1)
        """

        params = [query]

        if not self._pool:
            raise RuntimeError("Database pool is not available")

        if category:
            search_query += " AND category = $2"
            params.append(category)
            search_query += f" ORDER BY rank DESC LIMIT ${len(params) + 1}"
            params.append(str(limit))
        else:
            search_query += " ORDER BY rank DESC LIMIT $2"
            params.append(str(limit))

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(search_query, *params)

            return [
                KnowledgeItem(
                    id=row["id"],
                    title=row["title"],
                    content=row["content"],
                    category=row["category"],
                    tags=row["tags"] or [],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
                for row in rows
            ]

    async def get_by_category(
        self, category: str, limit: int = 10
    ) -> List[KnowledgeItem]:
        """カテゴリ別に取得。"""
        if not self._pool:
            await self.connect()

        if not self._pool:
            raise RuntimeError("Database pool is not available")

        query = """
        SELECT id, title, content, category, tags, created_at, updated_at
        FROM knowledge_base
        WHERE category = $1
        ORDER BY created_at DESC
        LIMIT $2
        """

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, category, limit)

            return [
                KnowledgeItem(
                    id=row["id"],
                    title=row["title"],
                    content=row["content"],
                    category=row["category"],
                    tags=row["tags"] or [],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
                for row in rows
            ]

    async def get_all_categories(self) -> List[str]:
        """利用可能なカテゴリ一覧を取得。"""
        if not self._pool:
            await self.connect()

        if not self._pool:
            raise RuntimeError("Database pool is not available")

        query = "SELECT DISTINCT category FROM knowledge_base ORDER BY category"

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query)
            return [row["category"] for row in rows]

    async def health_check(self) -> bool:
        """データベース接続確認。"""
        try:
            if not self._pool:
                await self.connect()

            if not self._pool:
                return False

            async with self._pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
                return True
        except Exception:
            return False
