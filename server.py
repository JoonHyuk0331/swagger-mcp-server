"""
Swagger MCP 서버 메인 (FastMCP 버전)
"""
import os
from typing import Optional
from mcp.server.fastmcp import FastMCP

from db import (
    init_db,
    list_endpoints as db_list_endpoints,
    get_endpoint_details as db_get_endpoint_details,
    get_schema as db_get_schema,
    list_versions as db_list_versions
)
from parser import parse_and_store_swagger

SWAGGER_URL = os.getenv("SWAGGER_URL", "http://localhost:8080/v3/api-docs")

# FastMCP 인스턴스 생성
mcp = FastMCP()


async def ensure_db_initialized():
    """DB 초기화 확인 (최초 1회만 실행)"""
    global _db_initialized
    if not _db_initialized:
        await init_db()
        _db_initialized = True


# DB 초기화 플래그
_db_initialized = False


@mcp.tool()
async def sync_swagger(version: Optional[str] = None) -> str:
    """Swagger JSON을 가져와 파싱하고 SQLite DB에 저장합니다.

    Args:
        version: API 버전 식별자 (선택사항)
    """
    await ensure_db_initialized()
    result = await parse_and_store_swagger(SWAGGER_URL, version)
    return (
        f"Swagger 동기화 완료\n\n"
        f"버전: {result['version']}\n"
        f"제목: {result['title']}\n"
        f"엔드포인트: {result['endpoints']}개\n"
        f"스키마: {result['schemas']}개"
    )


@mcp.tool()
async def list_endpoints(
    version: Optional[str] = None,
    path_pattern: Optional[str] = None,
    method: Optional[str] = None,
    tag: Optional[str] = None
) -> str:
    """저장된 API 엔드포인트 목록을 조회합니다.

    Args:
        version: API 버전 필터
        path_pattern: 경로 패턴 검색 (부분 일치)
        method: HTTP 메서드 (GET, POST 등)
        tag: 태그 필터
    """
    await ensure_db_initialized()
    endpoints = await db_list_endpoints(
        version=version,
        path_pattern=path_pattern,
        method=method,
        tag=tag
    )

    if not endpoints:
        return "조회된 엔드포인트가 없습니다."

    result_lines = [f"총 {len(endpoints)}개의 엔드포인트를 찾았습니다.\n"]
    for ep in endpoints:
        tags = ep.get("tags", "[]")
        result_lines.append(
            f"[{ep['id']}] {ep['method']} {ep['path']}\n"
            f"  - 요약: {ep.get('summary', 'N/A')}\n"
            f"  - 태그: {tags}\n"
            f"  - 버전: {ep['version']}\n"
        )

    return "\n".join(result_lines)


@mcp.tool()
async def get_endpoint_details(endpoint_id: int) -> str:
    """특정 엔드포인트의 상세 정보를 조회합니다.

    Args:
        endpoint_id: 엔드포인트 ID
    """
    await ensure_db_initialized()
    details = await db_get_endpoint_details(endpoint_id)

    if not details:
        return f"엔드포인트 ID {endpoint_id}를 찾을 수 없습니다."

    params = details.get("parameters", [])
    param_lines = []
    for p in params:
        required = "필수" if p["required"] else "선택"
        schema_ref = f" (스키마: {p['schema_ref']})" if p.get("schema_ref") else ""
        param_lines.append(
            f"  - {p['name']} ({p['in_type']}, {required}): {p['type']}{schema_ref}\n"
            f"    설명: {p.get('description', 'N/A')}"
        )

    return (
        f"엔드포인트 상세 정보\n\n"
        f"경로: {details['path']}\n"
        f"메서드: {details['method']}\n"
        f"요약: {details.get('summary', 'N/A')}\n"
        f"설명: {details.get('description', 'N/A')}\n"
        f"Operation ID: {details.get('operation_id', 'N/A')}\n"
        f"태그: {details.get('tags', 'N/A')}\n"
        f"버전: {details['version']}\n\n"
        f"파라미터:\n" + ("\n".join(param_lines) if param_lines else "  없음")
    )


@mcp.tool()
async def get_schema(version: str, schema_name: str) -> str:
    """특정 스키마의 정의를 조회합니다.

    Args:
        version: API 버전
        schema_name: 스키마 이름
    """
    await ensure_db_initialized()
    schema = await db_get_schema(version, schema_name)

    if not schema:
        return f"스키마 '{schema_name}' (버전: {version})를 찾을 수 없습니다."

    properties = schema.get("properties", {})
    required_fields = schema.get("required_fields", [])

    prop_lines = []
    for prop_name, prop_def in properties.items():
        is_required = "✓" if prop_name in required_fields else " "
        prop_type = prop_def.get("type", "unknown")
        description = prop_def.get("description", "")

        if prop_type == "ref":
            type_str = f"→ {prop_def.get('ref')}"
        elif prop_type == "array":
            type_str = f"array<{prop_def.get('items')}>"
        else:
            type_str = prop_type

        prop_lines.append(
            f"  [{is_required}] {prop_name}: {type_str}\n"
            f"      {description}"
        )

    return (
        f"스키마: {schema_name}\n\n"
        f"타입: {schema.get('type', 'object')}\n"
        f"설명: {schema.get('description', 'N/A')}\n\n"
        f"속성 ([✓] = 필수 필드):\n" + "\n".join(prop_lines)
    )


@mcp.tool()
async def list_versions() -> str:
    """저장된 모든 API 버전 목록을 조회합니다."""
    await ensure_db_initialized()
    versions = await db_list_versions()

    if not versions:
        return "저장된 API 버전이 없습니다."

    result_lines = [f"총 {len(versions)}개의 버전이 저장되어 있습니다.\n"]
    for v in versions:
        result_lines.append(
            f"버전: {v['version']}\n"
            f"  - 제목: {v['title']}\n"
            f"  - 동기화 시간: {v['synced_at']}\n"
            f"  - Base URL: {v.get('base_url', 'N/A')}\n"
        )

    return "\n".join(result_lines)


if __name__ == "__main__":
    # FastMCP 서버 실행
    mcp.run(transport="stdio")
