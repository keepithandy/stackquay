FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
RUN groupadd --system app && useradd --system --gid app --home /app app
COPY requirements.txt ./
RUN python -m pip install --require-hashes -r requirements.txt
COPY --chown=app:app . .
RUN mkdir -p /app/staticfiles && chown app:app /app/staticfiles
USER app
EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "30", "--max-requests", "1000", "--max-requests-jitter", "100", "--error-logfile", "-"]
