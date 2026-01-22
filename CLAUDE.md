# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Swagger API 문서 탐색용 MCP 서버입니다. Spring Boot 서버의 Swagger JSON을 파싱하여 SQLite DB에 저장하고, Claude가 MCP를 통해 DB를 조회하며 API 정보를 탐색합니다.

**핵심 가치**:
- As-is: LLM이 Swagger UI나 코드베이스를 일일이 읽어야 함 (부정확한 답변, 높은 토큰 사용량, 느린 응답)
- To-be: Claude가 자연어로 질문하면 MCP 도구들이 DB 쿼리로 빠르고 정확한 정보를 제공

## Development Setup

**Python Version**: 3.9+ (`.python-version`)
**Package Manager**: uv

## Tech Stack
            
- Python 3.9+
- SQLite
- aiosqlite
- httpx
- pydantic

**Core Dependencies**:
- `mcp` - Anthropic MCP SDK
- `pydantic` - 데이터 검증
- `httpx` - Swagger JSON 가져오기
- `aiosqlite` - 비동기 SQLite

## Project Structure

```
swagger-mcp-server/
├── server.py    # MCP 서버 메인
├── parser.py    # sync_swagger 구현
├── db.py        # DB 초기화 및 쿼리
└── pyproject.toml
```

## Core Features (5 MCP Tools)

1. **sync_swagger** - Swagger JSON 파싱 및 DB 저장
2. **list_endpoints** - API 엔드포인트 검색
3. **get_endpoint_details** - 엔드포인트 상세 조회
4. **get_schema** - 스키마 탐색
5. **list_versions** - API 문서 버전 관리

## Architecture

- **server.py**: MCP 서버의 진입점, 5개 도구(tool) 등록 및 요청 처리
- **parser.py**: Swagger JSON을 파싱하여 엔드포인트, 스키마, 파라미터 정보를 추출하고 DB에 저장
- **db.py**: SQLite 테이블 생성 및 CRUD 쿼리 함수들 (비동기 처리)
- DB는 엔드포인트, 스키마, 버전 정보를 구조화하여 저장하고, MCP 도구들이 효율적으로 조회

## Coding Style

**General Principles**:
- 모든 I/O 작업은 비동기(`async`/`await`)로 작성
- Pydantic 모델을 사용하여 데이터 검증 및 타입 안정성 확보
- 함수와 변수명은 명확하고 설명적으로 작성 (snake_case)

**Error Handling**:
- HTTP 요청 실패, DB 에러, JSON 파싱 에러 등 예상 가능한 예외 처리
- MCP 도구 함수에서 에러 발생 시 사용자에게 명확한 에러 메시지 반환
- 로깅을 통해 디버깅 정보 제공

**Database**:
- 모든 DB 쿼리는 `aiosqlite`로 비동기 처리
- 트랜잭션 관리 (여러 테이블에 데이터 삽입 시 atomic 보장)
- SQL injection 방지를 위해 파라미터화된 쿼리 사용

**MCP Tool Implementation**:
- 각 MCP 도구는 명확한 입력 파라미터 스키마 정의
- 도구 설명(description)은 한글로 작성하여 사용자가 이해하기 쉽게
- 도구 실행 결과는 JSON으로 직렬화 가능한 형태로 반환

**Code Organization**:
- 관련 기능은 모듈별로 분리 (server, parser, db)
- 재사용 가능한 유틸리티 함수는 별도 파일로 분리 가능
- 타입 힌트를 모든 함수 시그니처에 추가

## Git Workflow

**Branch Strategy**:
- `main` - 안정적인 프로덕션 코드
- 기능 개발 시 feature 브랜치 생성: `feature/tool-name` 또는 `feature/description`
- 버그 수정 시: `fix/issue-description`

**Commit Message Format**:
```
<type>: <subject>

[optional body]
```

Types:
- `feat`: 새로운 기능 추가 (e.g., `feat: add list_endpoints tool`)
- `fix`: 버그 수정
- `refactor`: 코드 리팩토링
- `docs`: 문서 수정
- `chore`: 빌드, 설정 파일 수정
- `test`: 테스트 코드 추가/수정

**Example Commits**:
```
feat: sync_swagger 파서 구현
```

**Before Committing**:
- 코드가 정상적으로 실행되는지 확인
- 타입 힌트가 올바른지 검증
- 불필요한 디버그 코드나 주석 제거
