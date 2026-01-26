# Swagger MCP Server

Swagger API 문서 탐색용 MCP 서버입니다. Spring Boot 서버의 Swagger JSON을 파싱하여 SQLite DB에 저장하고, Claude가 MCP를 통해 DB를 조회하며 API 정보를 탐색합니다.

## Why?

**핵심 가치**:
- As-is: LLM이 Swagger UI나 코드베이스를 일일이 읽어야 함 (부정확한 답변, 높은 토큰 사용량, 느린 응답)
- To-be: Claude가 자연어로 질문하면 MCP 도구들이 DB 쿼리로 빠르고 정확한 정보를 제공

## 설치

**요구사항**: Python 3.10+

```bash
# Python 3.10+ 설치 확인
python3 --version

# Python 3.10+가 없다면 설치 (macOS)
brew install python@3.12

# 가상 환경 생성
uv venv

# 가상 환경 활성화
source .venv/bin/activate

# 의존성 설치
uv pip install -e .
```

## 사용법

### 1. MCP 서버 실행

```bash
python server.py
```

### 2. 테스트 실행

**실제 Spring Boot 서버와 테스트**:
```bash
# Spring Boot 서버가 http://localhost:8080에서 실행 중이어야 함
python test_swagger.py
```

**샘플 데이터로 테스트**:
```bash
python test_swagger.py --sample
```

### 3-1. Claude Code Cli에서 사용

`claude_desktop_config.json`에 다음 설정 추가:

```json
{
  "mcpServers": {
    "swagger": {
      "command": "python",
      "args": ["/path/to/swagger-mcp-server/server.py"]
    }
  }
}
```

## MCP 도구 (Tools)

### 1. sync_swagger
Swagger JSON을 가져와 파싱하고 SQLite DB에 저장합니다.

```
swagger_url: http://localhost:8080/v3/api-docs
version: v1.0.0 (선택사항)
```

### 2. list_endpoints
저장된 API 엔드포인트 목록을 조회합니다.

**필터 옵션**:
- `version`: API 버전
- `path_pattern`: 경로 패턴 검색
- `method`: HTTP 메서드 (GET, POST 등)
- `tag`: 태그 필터

### 3. get_endpoint_details
특정 엔드포인트의 상세 정보를 조회합니다.

```
endpoint_id: 1
```

### 4. get_schema
특정 스키마의 정의를 조회합니다.

```
version: v1.0.0
schema_name: UserRequest
```

### 5. list_versions
저장된 모든 API 버전 목록을 조회합니다.

## 프로젝트 구조

```
swagger-mcp-server/
├── server.py         # MCP 서버 메인
├── parser.py         # Swagger JSON 파싱
├── db.py             # SQLite DB 관리
├── test_swagger.py   # 테스트 스크립트
├── pyproject.toml    # 프로젝트 설정
└── swagger.db        # SQLite 데이터베이스 (자동 생성)
```

## 예시

Claude Desktop에서 다음과 같이 사용할 수 있습니다:

```
"http://localhost:8080/v3/api-docs에서 Swagger를 동기화해줘"
→ sync_swagger 도구 실행

"GET 메서드 엔드포인트 목록을 보여줘"
→ list_endpoints 도구 실행 (method=GET)

"사용자 관련 API를 찾아줘"
→ list_endpoints 도구 실행 (path_pattern=user)

"엔드포인트 ID 5의 상세 정보를 알려줘"
→ get_endpoint_details 도구 실행

"UserRequest 스키마 구조를 보여줘"
→ get_schema 도구 실행
```