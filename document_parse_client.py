import os

import requests

from config import DOCUMENT_PARSE_MODEL, DOCUMENT_PARSE_URL, require_api_key


class DocumentParseError(RuntimeError):
    pass


def parse_document_to_text(file_path: str) -> str:
    api_key = require_api_key()

    with open(file_path, "rb") as f:
        files = {"document": (os.path.basename(file_path), f)}
        data = {"model": DOCUMENT_PARSE_MODEL, "output_formats": '["text"]'}
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.post(
            DOCUMENT_PARSE_URL, headers=headers, files=files, data=data, timeout=120
        )

    if response.status_code != 200:
        raise DocumentParseError(f"Document Parse API 오류 ({response.status_code}): {response.text}")

    return _extract_text(response.json())


def _extract_text(result: dict) -> str:
    # 공식 응답 스키마를 실API로 검증 못해서, top-level content{text}와 elements[]{content:{text}}
    # 두 형태를 모두 방어적으로 처리한다. 실제 응답을 받아보면 이 함수만 조정하면 됨.
    content = result.get("content")
    if isinstance(content, dict):
        text = content.get("text") or content.get("markdown") or content.get("html")
        if text:
            return text.strip()

    elements = result.get("elements")
    if isinstance(elements, list):
        parts = []
        for el in elements:
            el_content = el.get("content") or {}
            text = el_content.get("text") or el_content.get("markdown") or ""
            if text:
                parts.append(text)
        if parts:
            return "\n".join(parts).strip()

    raise DocumentParseError(f"Document Parse 응답에서 텍스트를 찾을 수 없습니다 (keys={list(result.keys())})")
