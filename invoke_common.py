import time
from typing import Callable, Optional

from pydantic import BaseModel

from hub_client import fetch_workflow, record_invocation
from job_state import finish_job, start_job


class InvokeRequest(BaseModel):
    report_id: str
    trace_id: Optional[str] = None
    request_id: Optional[str] = None


def run_invoke(
    req: InvokeRequest,
    agent_name: str,
    model: str,
    prompt_version: str,
    process_fn: Callable[[str], dict],
    result_message: str,
) -> dict:
    start_job(req.report_id)
    start_time = time.monotonic()
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
        )
        return {"status_code": 200, "message": result_message, "output": result}
    except Exception as e:
        record_invocation(
            report_id=req.report_id,
            agent_name=agent_name,
            status="FAILED",
            error={"message": str(e)},
        )
        return {"status_code": 500, "message": str(e), "output": {}}
    finally:
        finish_job()
