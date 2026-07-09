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
) -> None:
    # report_id가 없으면 어느 워크플로우에 기록할지 알 수 없어 스킵한다.
    if not report_id:
        return

    body = {"status": status}
    if output is not None:
        body["output"] = output
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
