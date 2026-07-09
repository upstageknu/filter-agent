from pathlib import Path

from document_parse_client import parse_document_to_text

DIRECT_TEXT_EXTENSIONS = {".md", ".txt"}
DOCUMENT_PARSE_EXTENSIONS = {".pdf", ".doc", ".docx", ".hwp", ".hwpx"}
TEXT_ENCODINGS = ("utf-8", "cp949", "euc-kr")


class UnsupportedFormatError(RuntimeError):
    pass


def _read_text_file(path: Path) -> str:
    for encoding in TEXT_ENCODINGS:
        try:
            return path.read_text(encoding=encoding).strip()
        except UnicodeDecodeError:
            continue
    raise UnsupportedFormatError(f"{path.name}의 인코딩을 확인할 수 없습니다")


def load_raw_report_text(file_path: str) -> str:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(file_path)

    ext = path.suffix.lower()
    if ext in DIRECT_TEXT_EXTENSIONS:
        return _read_text_file(path)
    if ext in DOCUMENT_PARSE_EXTENSIONS:
        return parse_document_to_text(str(path))

    supported = sorted(DIRECT_TEXT_EXTENSIONS | DOCUMENT_PARSE_EXTENSIONS)
    raise UnsupportedFormatError(f"지원하지 않는 형식입니다: {ext} (지원 형식: {supported})")
