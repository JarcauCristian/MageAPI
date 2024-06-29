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

RUN pip install -r requirements.txt

ENV API_KEY = key
ENV EMAIL = admin@admin.com
ENV PASSWORD = password
ENV BASE_URL = https://mage.sedimark.work
ENV LOCAL_IP = 127.0.0.1

EXPOSE 8000 

CMD ["python3", "main.py"]
