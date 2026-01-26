"""
Swagger JSON 파싱 및 DB 저장
"""
import httpx
from typing import Dict, Any, Optional
import logging

from db import (
    insert_version,
    get_version_id,
    insert_endpoint,
    insert_parameter,
    insert_schema,
    delete_version
)

logger = logging.getLogger(__name__)


async def fetch_swagger_json(url: str) -> Dict[str, Any]:
    """주어진 URL에서 Swagger JSON 가져오기 30초 넘어가면 타임아웃"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()


def extract_schema_ref(ref: str) -> str:
    """$ref에서 스키마 이름 추출"""
    if ref.startswith("#/components/schemas/"):
        return ref.replace("#/components/schemas/", "")
    return ref


async def parse_and_store_swagger(swagger_url: str, version_name: Optional[str] = None):
    """
    Swagger JSON을 파싱하고 DB에 저장

    Args:
        swagger_url: Swagger JSON URL (예: http://localhost:8080/v3/api-docs)
        version_name: 버전 식별자 (기본값: URL에서 추출)
    """
    try:
        # Swagger JSON 가져오기
        logger.info(f"Fetching Swagger JSON from {swagger_url}")
        swagger_data = await fetch_swagger_json(swagger_url)

        # 버전 정보 추출
        info = swagger_data.get("info", {})
        title = info.get("title", "Unknown API")
        description = info.get("description", "")
        api_version = version_name or info.get("version", "1.0.0")

        # 서버 URL 추출
        servers = swagger_data.get("servers", [])
        base_url = servers[0].get("url", "") if servers else ""

        logger.info(f"Parsing API: {title} (version: {api_version})")

        # 기존 버전 데이터 삭제 (재동기화)
        await delete_version(api_version)

        # 버전 정보 저장
        version_id = await insert_version(api_version, title, description, base_url)

        # 스키마 파싱 및 저장
        components = swagger_data.get("components", {})
        schemas = components.get("schemas", {})

        for schema_name, schema_def in schemas.items():
            await parse_schema(version_id, schema_name, schema_def)

        # 엔드포인트 파싱 및 저장
        paths = swagger_data.get("paths", {})
        endpoint_count = 0

        for path, path_item in paths.items():
            for method, operation in path_item.items():
                if method.lower() in ["get", "post", "put", "delete", "patch", "options", "head"]:
                    await parse_endpoint(version_id, path, method.upper(), operation)
                    endpoint_count += 1

        logger.info(f"Successfully stored {endpoint_count} endpoints and {len(schemas)} schemas")

        return {
            "version": api_version,
            "title": title,
            "endpoints": endpoint_count,
            "schemas": len(schemas)
        }

    except httpx.HTTPError as e:
        logger.error(f"HTTP error fetching Swagger JSON: {e}")
        raise Exception(f"Failed to fetch Swagger JSON: {str(e)}")
    except Exception as e:
        logger.error(f"Error parsing Swagger: {e}")
        raise Exception(f"Failed to parse Swagger: {str(e)}")


async def parse_schema(version_id: int, schema_name: str, schema_def: Dict[str, Any]):
    """스키마 정의 파싱 및 저장"""
    schema_type = schema_def.get("type", "object")
    properties = schema_def.get("properties", {})
    required_fields = schema_def.get("required", [])
    description = schema_def.get("description", "")

    # properties를 간단한 형태로 변환
    simplified_properties = {}
    for prop_name, prop_def in properties.items():
        prop_type = prop_def.get("type", "unknown")
        prop_ref = prop_def.get("$ref", "")

        if prop_ref:
            simplified_properties[prop_name] = {
                "type": "ref",
                "ref": extract_schema_ref(prop_ref),
                "description": prop_def.get("description", "")
            }
        elif prop_type == "array":
            items = prop_def.get("items", {})
            items_ref = items.get("$ref", "")
            simplified_properties[prop_name] = {
                "type": "array",
                "items": extract_schema_ref(items_ref) if items_ref else items.get("type", "unknown"),
                "description": prop_def.get("description", "")
            }
        else:
            simplified_properties[prop_name] = {
                "type": prop_type,
                "description": prop_def.get("description", ""),
                "format": prop_def.get("format", "")
            }

    await insert_schema(
        version_id,
        schema_name,
        schema_type,
        simplified_properties,
        required_fields,
        description
    )


async def parse_endpoint(version_id: int, path: str, method: str, operation: Dict[str, Any]):
    """엔드포인트 정보 파싱 및 저장"""
    summary = operation.get("summary", "")
    description = operation.get("description", "")
    operation_id = operation.get("operationId", "")
    tags = operation.get("tags", [])
    deprecated = operation.get("deprecated", False)

    # 엔드포인트 저장
    endpoint_id = await insert_endpoint(
        version_id,
        path,
        method,
        summary,
        description,
        operation_id,
        tags,
        deprecated
    )

    # 파라미터 파싱
    parameters = operation.get("parameters", [])
    for param in parameters:
        await parse_parameter(endpoint_id, param)

    # Request Body 파싱 (POST, PUT 등)
    request_body = operation.get("requestBody", {})
    if request_body:
        content = request_body.get("content", {})
        for content_type, content_def in content.items():
            schema = content_def.get("schema", {})
            ref = schema.get("$ref", "")

            if ref:
                await insert_parameter(
                    endpoint_id,
                    "requestBody",
                    "body",
                    request_body.get("required", False),
                    content_type,
                    request_body.get("description", ""),
                    extract_schema_ref(ref)
                )


async def parse_parameter(endpoint_id: int, param: Dict[str, Any]):
    """파라미터 정보 파싱 및 저장"""
    name = param.get("name", "")
    in_type = param.get("in", "")
    required = param.get("required", False)
    description = param.get("description", "")

    schema = param.get("schema", {})
    param_type = schema.get("type", "string")
    ref = schema.get("$ref", "")

    await insert_parameter(
        endpoint_id,
        name,
        in_type,
        required,
        param_type,
        description,
        extract_schema_ref(ref) if ref else None
    )
