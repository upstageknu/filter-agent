import copy

FILTER_OUTPUT_TEMPLATE = {
    "is_bug_report": None,
    "confidence": None,
    "reason": None,
}

PARSER_OUTPUT_TEMPLATE = {
    "reporter": {
        "name": None,
        "team": None,
        "contacts": [],
    },
    "title": None,
    "vuln_type": None,
    "affected_software": None,
    "affected_version": None,
    "summary": None,
    "cited_user_defined_functions": [],
    "cited_library_functions": [],
    "function_calls": [],
    "cited_headers": [],
    "cited_commits": [],
    "poc_present": False,
    "poc_code": None,
    "repro_steps": [],
    "claimed_impact": [],
}

# fact_check / dedup / debate는 다른 팀원 소관 agent. 팀이 합의한 초기 스켈레톤 값을 그대로 옮겨서
# 전체 report JSON 계약(global object)의 모양을 처음부터 끝까지 유지한다.
FACT_CHECK_TEMPLATE = {
    "function_check": [],
    "file_check": [],
    "header_check": [],
    "commit_check": [],
    "function_call_check": [],
    "poc_check": {"compilable": None, "compile_error": None},
    "reachability": {"verdict": "UNKNOWN", "reason": None},
    "summary": None,
}

DEDUP_TEMPLATE = {
    "signature": None,
    "matches": [],
    "verdict": None,
    "duplicate_of": None,
}

DEBATE_TEMPLATE = {
    "debate_logs": [],
    "vulnerable_agent": {
        "position": "VULNERABLE",
        "argument": None,
        "evidence": [],
        "weaknesses": [],
        "strength": None,
        "confidence": None,
    },
    "not_vulnerable_agent": {
        "position": "NOT_VULNERABLE",
        "argument": None,
        "evidence": [],
        "weaknesses": [],
        "strength": None,
        "confidence": None,
    },
    "judge": {
        "verdict": None,
        "winning_side": None,
        "reason": None,
        "confidence": None,
        "next_step": None,
    },
}


def normalize_filter_output(raw: dict) -> dict:
    result = copy.deepcopy(FILTER_OUTPUT_TEMPLATE)
    result["is_bug_report"] = bool(raw.get("is_bug_report", False))
    result["confidence"] = float(raw.get("confidence", 0.0))
    result["reason"] = raw.get("reason")
    return result


def normalize_parser_output(raw: dict) -> dict:
    result = copy.deepcopy(PARSER_OUTPUT_TEMPLATE)

    reporter = raw.get("reporter") or {}
    result["reporter"]["name"] = reporter.get("name")
    result["reporter"]["team"] = reporter.get("team")
    result["reporter"]["contacts"] = reporter.get("contacts") or []

    for key in ("title", "vuln_type", "affected_software", "affected_version", "summary", "poc_code"):
        result[key] = raw.get(key)

    for key in (
        "cited_user_defined_functions",
        "cited_library_functions",
        "function_calls",
        "cited_headers",
        "cited_commits",
        "repro_steps",
        "claimed_impact",
    ):
        result[key] = raw.get(key) or []

    result["poc_present"] = bool(raw.get("poc_present", False))
    return result


def build_report_skeleton(report_id: str, created_at: str, raw_report_txt: str) -> dict:
    return {
        "report_id": report_id,
        "workflow_status": "RUNNING",
        "created_at": created_at,
        "input": {"raw_report_txt": raw_report_txt},
        "agent_results": {
            "bug_report_checker": copy.deepcopy(FILTER_OUTPUT_TEMPLATE),
            "parser": copy.deepcopy(PARSER_OUTPUT_TEMPLATE),
            "fact_check": copy.deepcopy(FACT_CHECK_TEMPLATE),
            "dedup": copy.deepcopy(DEDUP_TEMPLATE),
            "debate": copy.deepcopy(DEBATE_TEMPLATE),
        },
    }
