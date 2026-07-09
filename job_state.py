_state = {"status": "ready", "job_id": None}


def start_job(job_id):
    _state["status"] = "working"
    _state["job_id"] = job_id


def finish_job():
    _state["status"] = "ready"
    _state["job_id"] = None


def health_payload():
    if _state["status"] == "working":
        return {"status": f"working ({_state['job_id']})"}
    return {"status": "ready"}
