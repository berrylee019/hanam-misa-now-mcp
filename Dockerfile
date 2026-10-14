FROM python:3.11-slim
WORKDIR /app
COPY main.py .
RUN pip install fastmcp
EXPOSE 8080
CMD ["python", "main.py"]
