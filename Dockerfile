FROM python:3.9-slim

WORKDIR /app/AlertTool

COPY src /app/AlertTool/src

COPY requirements.txt /app/AlertTool

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "src/main.py"]