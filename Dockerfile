FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY config.py utils.py schemas.py job_state.py hub_client.py invoke_common.py \
     document_parse_client.py input_pipeline.py \
     bug_report_filter.py filter_service.py ./

EXPOSE 8000

CMD ["uvicorn", "filter_service:app", "--host", "0.0.0.0", "--port", "8000"]
