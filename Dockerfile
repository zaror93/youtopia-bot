FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install requests python-telegram-bot schedule

COPY main.py .

CMD ["python", "main.py"]
