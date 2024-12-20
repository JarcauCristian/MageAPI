FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN apt-get update && \
    apt-get install -y \
        build-essential \
        make \
        gcc \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

RUN pip install -r requirements.txt

ENV EMAIL = admin@admin.com
ENV PASSWORD = password
ENV BASE_URL = https://mage.sedimark.work
ENV AUTH = false
ENV OLLAMA_URL = http://localhost:11434

EXPOSE 8000 

CMD ["python3", "main.py"]
