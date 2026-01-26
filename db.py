"""
SQLite 데이터베이스 초기화 및 쿼리 함수
"""
import aiosqlite
from typing import List, Dict, Any, Optional
import json


DB_PATH = "/Users/kimjunhyuk/Desktop/swagger-mcp-server/swagger.db"


async def init_db():
    """데이터베이스 초기화 및 테이블 생성"""
    async with aiosqlite.connect(DB_PATH) as db:
        # 버전 테이블
        await db.execute("""
            CREATE TABLE IF NOT EXISTS versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version TEXT NOT NULL UNIQUE,
                title TEXT,
                description TEXT,
                base_url TEXT,
                synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 엔드포인트 테이블
        await db.execute("""
            CREATE TABLE IF NOT EXISTS endpoints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version_id INTEGER NOT NULL,
                path TEXT NOT NULL,
                method TEXT NOT NULL,
                summary TEXT,
                description TEXT,
                operation_id TEXT,
                tags TEXT,
                deprecated INTEGER DEFAULT 0,
                FOREIGN KEY (version_id) REFERENCES versions (id),
                UNIQUE(version_id, path, method)
            )
        """)

        # 파라미터 테이블
        await db.execute("""
            CREATE TABLE IF NOT EXISTS parameters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endpoint_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                in_type TEXT NOT NULL,
                required INTEGER DEFAULT 0,
                type TEXT,
                description TEXT,
                schema_ref TEXT,
                FOREIGN KEY (endpoint_id) REFERENCES endpoints (id)
            )
        """)

        # 스키마 테이블
        await db.execute("""
            CREATE TABLE IF NOT EXISTS schemas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                type TEXT,
                properties TEXT,
                required_fields TEXT,
                description TEXT,
                FOREIGN KEY (version_id) REFERENCES versions (id),
                UNIQUE(version_id, name)
            )
        """)

        # 인덱스 생성
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_endpoints_version
            ON endpoints(version_id)
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_endpoints_path
            ON endpoints(path)
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_schemas_version
            ON schemas(version_id)
        """)

        await db.commit()


async def insert_version(version: str, title: str, description: str, base_url: str) -> int:
    """새 버전 정보 삽입"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            INSERT OR REPLACE INTO versions (version, title, description, base_url)
            VALUES (?, ?, ?, ?)
            """,
            (version, title, description, base_url)
        )
        await db.commit()
        return cursor.lastrowid


async def get_version_id(version: str) -> Optional[int]:
    """버전 문자열로 버전 ID 조회"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id FROM versions WHERE version = ?",
            (version,)
        )
        row = await cursor.fetchone()
        return row[0] if row else None


async def insert_endpoint(
    version_id: int,
    path: str,
    method: str,
    summary: str,
    description: str,
    operation_id: str,
    tags: List[str],
    deprecated: bool = False
) -> int:
    """엔드포인트 정보 삽입"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            INSERT OR REPLACE INTO endpoints
            (version_id, path, method, summary, description, operation_id, tags, deprecated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (version_id, path, method, summary, description, operation_id,
             json.dumps(tags), 1 if deprecated else 0)
        )
        await db.commit()
        return cursor.lastrowid


async def insert_parameter(
    endpoint_id: int,
    name: str,
    in_type: str,
    required: bool,
    param_type: str,
    description: str,
    schema_ref: Optional[str] = None
):
    """파라미터 정보 삽입"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO parameters
            (endpoint_id, name, in_type, required, type, description, schema_ref)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (endpoint_id, name, in_type, 1 if required else 0, param_type, description, schema_ref)
        )
        await db.commit()


async def insert_schema(
    version_id: int,
    name: str,
    schema_type: str,
    properties: Dict[str, Any],
    required_fields: List[str],
    description: str
):
    """스키마 정보 삽입"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT OR REPLACE INTO schemas
            (version_id, name, type, properties, required_fields, description)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (version_id, name, schema_type, json.dumps(properties),
             json.dumps(required_fields), description)
        )
        await db.commit()


async def list_endpoints(
    version: Optional[str] = None,
    path_pattern: Optional[str] = None,
    method: Optional[str] = None,
    tag: Optional[str] = None
) -> List[Dict[str, Any]]:
    """엔드포인트 목록 조회"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        query = """
            SELECT e.*, v.version
            FROM endpoints e
            JOIN versions v ON e.version_id = v.id
            WHERE 1=1
        """
        params = []

        if version:
            query += " AND v.version = ?"
            params.append(version)

        if path_pattern:
            query += " AND e.path LIKE ?"
            params.append(f"%{path_pattern}%")

        if method:
            query += " AND e.method = ?"
            params.append(method.upper())

        if tag:
            query += " AND e.tags LIKE ?"
            params.append(f"%{tag}%")

        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()

        return [dict(row) for row in rows]


async def get_endpoint_details(endpoint_id: int) -> Optional[Dict[str, Any]]:
    """엔드포인트 상세 정보 조회 (파라미터 포함)"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        # 엔드포인트 기본 정보
        cursor = await db.execute(
            """
            SELECT e.*, v.version
            FROM endpoints e
            JOIN versions v ON e.version_id = v.id
            WHERE e.id = ?
            """,
            (endpoint_id,)
        )
        endpoint = await cursor.fetchone()

        if not endpoint:
            return None

        # 파라미터 정보
        cursor = await db.execute(
            "SELECT * FROM parameters WHERE endpoint_id = ?",
            (endpoint_id,)
        )
        parameters = await cursor.fetchall()

        result = dict(endpoint)
        result["parameters"] = [dict(p) for p in parameters]

        return result


async def get_schema(version: str, schema_name: str) -> Optional[Dict[str, Any]]:
    """스키마 정보 조회"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        cursor = await db.execute(
            """
            SELECT s.*
            FROM schemas s
            JOIN versions v ON s.version_id = v.id
            WHERE v.version = ? AND s.name = ?
            """,
            (version, schema_name)
        )
        row = await cursor.fetchone()

        if not row:
            return None

        result = dict(row)
        if result.get("properties"):
            result["properties"] = json.loads(result["properties"])
        if result.get("required_fields"):
            result["required_fields"] = json.loads(result["required_fields"])

        return result


async def list_versions() -> List[Dict[str, Any]]:
    """저장된 모든 버전 목록 조회"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        cursor = await db.execute(
            "SELECT * FROM versions ORDER BY synced_at DESC"
        )
        rows = await cursor.fetchall()

        return [dict(row) for row in rows]


async def delete_version(version: str):
    """버전 및 관련 데이터 삭제"""
    async with aiosqlite.connect(DB_PATH) as db:
        version_id = await get_version_id(version)

        if not version_id:
            return

        # 파라미터 삭제
        await db.execute(
            """
            DELETE FROM parameters
            WHERE endpoint_id IN (
                SELECT id FROM endpoints WHERE version_id = ?
            )
            """,
            (version_id,)
        )

        # 엔드포인트 삭제
        await db.execute(
            "DELETE FROM endpoints WHERE version_id = ?",
            (version_id,)
        )

        # 스키마 삭제
        await db.execute(
            "DELETE FROM schemas WHERE version_id = ?",
            (version_id,)
        )

        # 버전 삭제
        await db.execute(
            "DELETE FROM versions WHERE id = ?",
            (version_id,)
        )

        await db.commit()
