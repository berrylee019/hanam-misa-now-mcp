FROM python:3.11-slim
WORKDIR /app
COPY main.py .
RUN pip install --no-cache-dir fastmcp uvicorn
EXPOSE 8000
CMD ["python", "main.py"]
