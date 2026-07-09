import base64
import os
import tempfile
import time
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from bug_report_filter import check_bug_report
from config import SOLAR_MODEL
from hub_client import record_invocation
from input_pipeline import UnsupportedFormatError, load_raw_report_text
from invoke_common import InvokeRequest, run_invoke
from job_state import finish_job, health_payload, start_job

AGENT_NAME = "bug_report_checker"

app = FastAPI(title="bug-report-filter")

PROMPT_VERSION = "filter-v1"


class FilterRequest(BaseModel):
    job_id: Optional[str] = None
    report_id: Optional[str] = None
    raw_report_txt: Optional[str] = None
    file_name: Optional[str] = None
    file_base64: Optional[str] = None


@app.get("/health")
def health():
    return health_payload()


@app.post("/invoke")
def invoke_endpoint(req: InvokeRequest):
    return run_invoke(
        req, AGENT_NAME, SOLAR_MODEL, PROMPT_VERSION, check_bug_report, "filter completed"
    )


@app.post("/filter")
def filter_endpoint(req: FilterRequest):
    start_job(req.job_id)
    start_time = time.monotonic()
    try:
        raw_text = _resolve_raw_text(req)
        filter_result = check_bug_report(raw_text)
        duration_ms = int((time.monotonic() - start_time) * 1000)

        record_invocation(
            report_id=req.report_id,
            agent_name=AGENT_NAME,
            status="SUCCEEDED",
            output=filter_result,
            model=SOLAR_MODEL,
            prompt_version=PROMPT_VERSION,
            duration_ms=duration_ms,
        )
        return {
            "job_id": req.job_id,
            "report_id": req.report_id,
            "raw_report_txt": raw_text,
            "bug_report_checker": filter_result,
            "model": SOLAR_MODEL,
            "prompt_version": PROMPT_VERSION,
        }
    except UnsupportedFormatError as e:
        record_invocation(
            report_id=req.report_id,
            agent_name=AGENT_NAME,
            status="FAILED",
            error={"message": str(e)},
        )
        raise HTTPException(status_code=422, detail=str(e))
    finally:
        finish_job()


def _resolve_raw_text(req: FilterRequest) -> str:
    if req.raw_report_txt is not None:
        return req.raw_report_txt

    if req.file_base64 and req.file_name:
        suffix = os.path.splitext(req.file_name)[1]
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(base64.b64decode(req.file_base64))
            tmp_path = tmp.name
        try:
            return load_raw_report_text(tmp_path)
        finally:
            os.unlink(tmp_path)

    raise HTTPException(
        status_code=422, detail="raw_report_txt 또는 file_base64+file_name 중 하나는 필요합니다"
    )
