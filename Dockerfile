FROM python:3.14-slim
WORKDIR /app
COPY commit_lint ./commit_lint
ENV PYTHONPATH=/app
ENTRYPOINT ["python3", "-m", "commit_lint"]
