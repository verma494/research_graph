FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH=/app/src

# Keep container running for interactive shell access
CMD ["tail", "-f", "/dev/null"]
