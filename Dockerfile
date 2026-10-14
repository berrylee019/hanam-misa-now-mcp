FROM python:3.11-slim
WORKDIR /app
COPY main.py .
RUN pip install fastmcp
CMD ["python", "main.py"]
