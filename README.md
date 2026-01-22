# Summary
Swagger API 문서 탐색용 MCP 서버입니다. Spring Boot 서버의 Swagger JSON을 파싱하여 SQLite DB에 저장하고, Claude가 MCP를 통해 DB를 조회하며 API 정보를 탐색합니다.

## Why?
**핵심 가치**:
- As-is: LLM이 Swagger UI나 코드베이스를 일일이 읽어야 함 (부정확한 답변, 높은 토큰 사용량, 느린 응답)
- To-be: Claude가 자연어로 질문하면 MCP 도구들이 DB 쿼리로 빠르고 정확한 정보를 제공

Install dependencies:
```bash
uv pip install -e .
```