FROM python:3.11-slim

WORKDIR /app

COPY ./src/ .
COPY ./requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

ARG APP_PROFILE=ZA_CLOUD

ENV APP_PROFILE=$APP_PROFILE

ENTRYPOINT ["python", "main.py"]