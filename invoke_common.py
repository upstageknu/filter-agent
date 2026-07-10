import json
import time
from typing import Callable, Optional

from pydantic import BaseModel

from hub_client import emit_event, fetch_job_id, fetch_workflow, record_invocation
from job_state import finish_job, start_job


class InvokeRequest(BaseModel):
    report_id: str
    trace_id: Optional[str] = None
    request_id: Optional[str] = None
    agent_job_id: Optional[int] = None


def _brief(result: dict, max_len: int = 300) -> str:
    """관리자 확인용 한 줄 요약(길게 남길 필요 없음 - 핵심 결과값만)."""
    try:
        text = json.dumps(result, ensure_ascii=False)
    except (TypeError, ValueError):
        text = str(result)
    return text if len(text) <= max_len else text[:max_len] + "..."


def run_invoke(
    req: InvokeRequest,
    agent_name: str,
    model: str,
    prompt_version: str,
    process_fn: Callable[[str], dict],
    result_message: str,
) -> dict:
    start_job(req.agent_job_id or req.request_id or req.report_id)
    start_time = time.monotonic()
    job_id = req.agent_job_id or fetch_job_id(req.report_id, agent_name)
    emit_event(
        report_id=req.report_id,
        agent_name=agent_name,
        event_type="agent.start",
        message=f"{agent_name} 시작",
        trace_id=req.trace_id,
        request_id=req.request_id,
        agent_job_id=job_id,
    )
    try:
        workflow = fetch_workflow(req.report_id)
        raw_text = (workflow.get("input") or {}).get("raw_report_txt")
        if not raw_text:
            raise ValueError("workflow.input.raw_report_txt가 비어있습니다")

        result = process_fn(raw_text)
        duration_ms = int((time.monotonic() - start_time) * 1000)

        record_invocation(
            report_id=req.report_id,
            agent_name=agent_name,
            status="SUCCEEDED",
            output=result,
            model=model,
            prompt_version=prompt_version,
            duration_ms=duration_ms,
            message=result_message,
            trace_id=req.trace_id,
            request_id=req.request_id,
            agent_job_id=job_id,
        )
        emit_event(
            report_id=req.report_id,
            agent_name=agent_name,
            event_type="agent.end",
            message=f"{agent_name} 완료 ({duration_ms}ms): {_brief(result)}",
            payload={"duration_ms": duration_ms},
            trace_id=req.trace_id,
            request_id=req.request_id,
            agent_job_id=job_id,
        )
        return {"status_code": 200, "message": result_message, "output": result}
    except Exception as e:
        record_invocation(
            report_id=req.report_id,
            agent_name=agent_name,
            status="FAILED",
            error={"message": str(e)},
            message=f"{agent_name} failed: {e}",
            trace_id=req.trace_id,
            request_id=req.request_id,
            agent_job_id=job_id,
        )
        emit_event(
            report_id=req.report_id,
            agent_name=agent_name,
            event_type="agent.error",
            message=f"{agent_name} 실패: {e}",
            level="ERROR",
            trace_id=req.trace_id,
            request_id=req.request_id,
            agent_job_id=job_id,
        )
        return {"status_code": 500, "message": str(e), "output": None}
    finally:
        finish_job()
