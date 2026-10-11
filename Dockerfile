FROM python:3.12-slim
WORKDIR /opt/ryzenc2
COPY requirements.txt .
RUN pip install --no-cache-dir colorama requests python-dotenv || true
COPY . .
EXPOSE 8080
CMD ["python3", "app.py"]
