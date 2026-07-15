# filter-agent

버그바운티 파이프라인의 input 정규화 + 버그 리포트 형식 필터 agent.
Upstage Document Parse(문서 → 텍스트)와 Solar Pro 3(필터 LLM)를 사용한다.

## 로컬 실행

```powershell
pip install -r requirements.txt
copy .env.example .env   # UPSTAGE_API_KEY 채워 넣기
uvicorn filter_service:app --host 0.0.0.0 --port 8000
```

## 엔드포인트

- `GET /health` — `{"status": "ready"}` 또는 `{"status": "working (job-id)"}`
- `POST /invoke` — 오케스트레이터가 호출하는 표준 엔드포인트.
  ```json
  { "report_id": "RPT-CURL-0001", "trace_id": "...", "request_id": "..." }
  ```
  `report_id`로 허브(`GET /db/workflows/{report_id}`)에서 `input.raw_report_txt`를 직접 조회해 처리한다.
  응답: `{"status_code": 200, "message": "filter completed", "output": {...}}`
- `POST /filter` — 로컬 테스트/수동 호출용. `raw_report_txt` 또는 `file_base64`+`file_name`을 직접 받는다.

## Docker

```powershell
docker build -t filter-agent .
docker run --env-file .env -p 8000:8000 filter-agent
```

이 레포는 PM 플랫폼과 Git 연동돼 있어, `main` 브랜치에 push하면 자동 빌드+배포된다.

## 동작

1. 파일/텍스트 → `raw_report_txt` (Document Parse 또는 직접 읽기)
2. 필터 agent(Solar Pro 3) → `is_bug_report`/`confidence`/`reason` 판단.
   `is_bug_report: false`인데 `confidence`가 `FILTER_REJECT_CONFIDENCE_THRESHOLD`(기본 0.6) 미만이면
   애매한 것으로 보고 통과시킨다 (반려는 "아님"을 확신할 때만).
3. 처리 결과를 허브의 `POST /db/workflows/{report_id}/agents/bug_report_checker/invocations`로 기록.
