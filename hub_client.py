from typing import Optional

import requests

from config import HUB_BASE_URL


def fetch_workflow(report_id: str) -> dict:
    url = f"{HUB_BASE_URL}/db/workflows/{report_id}"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()["workflow"]


def record_invocation(
    report_id: Optional[str],
    agent_name: str,
    status: str,
    output: Optional[dict] = None,
    error: Optional[dict] = None,
    model: Optional[str] = None,
    prompt_version: Optional[str] = None,
    duration_ms: Optional[int] = None,
    message: Optional[str] = None,
    trace_id: Optional[str] = None,
    request_id: Optional[str] = None,
    agent_job_id: Optional[int] = None,
    token_usage: Optional[dict] = None,
) -> None:
    # report_id가 없으면 어느 워크플로우에 기록할지 알 수 없어 스킵한다.
    if not report_id:
        return

    succeeded = status.upper() in {"SUCCEEDED", "SUCCESS"}
    result_message = message or f"{agent_name} {'completed' if succeeded else 'failed'}"
    body = {
        "status_code": 200 if succeeded else 500,
        "message": result_message,
        "output": output if succeeded else None,
        "trace_id": trace_id,
        "request_id": request_id,
        "request_payload": {
            "report_id": report_id,
            "trace_id": trace_id,
            "request_id": request_id,
        },
        "response_payload": {
            "status_code": 200 if succeeded else 500,
            "message": result_message,
            "output": output if succeeded else None,
        },
        "token_usage": token_usage or {},
    }
    if agent_job_id is not None:
        body["agent_job_id"] = agent_job_id
    if error is not None:
        body["error"] = error
    if model:
        body["model"] = model
    if prompt_version:
        body["prompt_version"] = prompt_version
    if duration_ms is not None:
        body["duration_ms"] = duration_ms

    url = f"{HUB_BASE_URL}/db/workflows/{report_id}/agents/{agent_name}/invocations"
    try:
        requests.post(url, json=body, timeout=10)
    except requests.RequestException:
        # 허브 기록이 실패해도 우리 자신의 동기 응답은 정상적으로 리턴한다 (best-effort).
        pass


def fetch_job_id(report_id: Optional[str], agent_name: str) -> Optional[int]:
    """이 report_id/agent_name에 해당하는 가장 최근 agent_job의 id를 조회한다.

    이벤트 로그(POST .../events)는 agent_job_id가 실제로 존재하는 job을 가리켜야
    허브가 받아준다(0이나 없는 값은 404) - best-effort이므로 실패 시 None을 반환한다.
    """
    if not report_id:
        return None
    url = f"{HUB_BASE_URL}/db/workflows/{report_id}/jobs"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        jobs = [j for j in response.json().get("agent_jobs", []) if j.get("agent_name") == agent_name]
        if not jobs:
            return None
        return max(j["id"] for j in jobs)
    except requests.RequestException:
        return None


def emit_event(
    report_id: Optional[str],
    agent_name: str,
    event_type: str,
    message: Optional[str] = None,
    payload: Optional[dict] = None,
    level: str = "INFO",
    trace_id: Optional[str] = None,
    request_id: Optional[str] = None,
    agent_job_id: Optional[int] = None,
) -> None:
    if not report_id:
        return

    body = {"event_type": event_type, "level": level, "source": "agent"}
    if message:
        body["message"] = message
    if payload is not None:
        body["payload"] = payload
    if trace_id:
        body["trace_id"] = trace_id
    if request_id:
        body["request_id"] = request_id
    if agent_job_id is not None:
        body["agent_job_id"] = agent_job_id

    url = f"{HUB_BASE_URL}/db/workflows/{report_id}/agents/{agent_name}/events"
    try:
        requests.post(url, json=body, timeout=10)
    except requests.RequestException:
        # 디버그 로그 기록 실패는 무시한다 (best-effort).
        pass
