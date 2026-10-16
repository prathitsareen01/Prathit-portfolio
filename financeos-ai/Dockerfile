FROM python:3.14-slim
WORKDIR /app
COPY requirements-runtime.txt .
RUN pip install --no-cache-dir -r requirements-runtime.txt
COPY financeos ./financeos
COPY demo ./demo
RUN useradd --create-home financeos && chown -R financeos:financeos /app
USER financeos
ENV PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["sh", "-c", "exec python -m uvicorn financeos.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
